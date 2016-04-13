from .util import json_load, json_loads, json_dump, read
from argparse import ArgumentParser
import logging, hashlib
from sys import stdout
from os import path, makedirs


class Pipeline(object):
    """
    Pipeline for processing data. Each command is implemented as an instance method without arguments.

    Parameters
    ----------
    name : str
        name of the pipeline
    logging_level : int
        logging level for the pipeline
    """
    def __init__(self, name, logging_level=logging.INFO):
        self.name = name
        self.configuration = None
        self.configuration_hash = None
        self.arguments = None
        self.result = None

        # Set up the argument parser
        self.argument_parser = ArgumentParser(name)
        self.argument_parser.add_argument('--force', '-f', help='reevaluate all commands', action='store_true',
                                          default=False)
        self.argument_parser.add_argument('configuration_file', type=str, help='path to a JSON configuration file')
        self.argument_parser.add_argument('commands', type=str, nargs='+', help='commands to evaluate')

        # Set up logging
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging_level)
        self.logger.addHandler(logging.StreamHandler(stdout))

    def _default_configuration(self):
        """
        Get the default configuration.
        """
        return {}

    def _load_configuration(self):
        """
        Load the configuration file.
        """
        configuration = self._default_configuration()

        # Load the configuration and compute the hash
        try:
            text = read(self.arguments.configuration_file)
            configuration.update(json_loads(text))
            configuration_hash = hashlib.sha256(text).hexdigest()
        except IOError as ex:
            self.logger.critical(ex.message)
            raise

        # Update the output file
        if 'result_file' not in configuration:
            base, ext = path.split(self.arguments.configuration_file)
            configuration['result_file'] = base + '_result.json'

        return configuration, configuration_hash

    def _load_result(self):
        """
        Load the previous result file and ensure the configuration matches.
        """
        if path.exists(self.configuration['result_file']):
            result = json_load(self.configuration['result_file'])

            if result['configuration']['hash'] != self.configuration_hash:
                self.logger.info('configuration hash mismatch; deleting previous results')
        else:
            result = {}

        result['configuration'] = {
            'hash': self.configuration_hash,
            'path': path.abspath(self.arguments.configuration_file),
        }

        return result

    def _dump_result(self):
        """
        Dump the result of the pipeline to disk.
        """
        # Ensure the directory exists
        makedirs(path.dirname(self.configuration['result_file']))
        json_dump(self.result, self.configuration['result_file'])

    def run(self):
        """
        Run the pipeline.
        """
        # Get the arguments
        self.arguments = self.argument_parser.parse_args()
        # Load the configuration
        self.configuration, self.configuration_hash = self._load_configuration()
        # Get previous results
        self.result = self._load_result()
        # Iterate over all commands and execute them
        for command in self.arguments.commands:
            self.result[command] = self._evaluate(command)

        self.logger.info('Exit')

    def _evaluate(self, command):
        """
        Evaluate a command.

        Parameters
        ----------
        command : str
            name of the command to evaluate
        """
        # Check the command exists
        if command not in self._commands:
            msg = "'{}' is not a recognised command".format(command)
            self.logger.critical(msg)
            raise KeyError(msg)

        # Check whether the commands have already been evaluated
        if command in self.result and not self.arguments.force:
            self.logger.info("command '{}' has already been evaluated".format(command))
            return
        else:
            self.logger.info("begin command '{}'".format(command))

        # Execute the command
        result = self._commands[command]()

        self.logger.info("end command '{}'".format(command))
        return result

    @property
    def _commands(self):
        """
        Get a dictionary of command names and implementations.
        """
        raise NotImplementedError
