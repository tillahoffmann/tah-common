from .util import json_load, json_loads, json_dump, read, recursive_update, mkdir_p, json_dumps, StringEncoder
from argparse import ArgumentParser
import logging, hashlib
from sys import stdout
from os import path
from time import time


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
    def __init__(self, name):
        self.name = name
        self.configuration = None
        self.configuration_hash = None
        self.arguments = None
        self.result = None

        # Set up the argument parser
        self.argument_parser = ArgumentParser(name)
        self.argument_parser.add_argument('--force', '-f', help='reevaluate all commands', action='store_true',
                                          default=False)
        self.argument_parser.add_argument('--out', '-o', help="override output filename", type=str)
        self.argument_parser.add_argument('--level', '-l', help='logging level', default='info',
                                          choices=['debug', 'info', 'warning', 'error', 'critical'])
        self.argument_parser.add_argument('--repeat', '-r', help='number of independent repetitions to run', type=int)
        self.argument_parser.add_argument('configuration_file', type=str, help='path to a JSON configuration file')
        self.argument_parser.add_argument('commands', type=str, nargs='+', help='commands to evaluate')

        self.logger = logging.getLogger(self.name)
        self._timings = {}

    def _begin(self, name):
        self._timings[name] = time()
        self.logger.info("begin " + name)

    def _end(self, name):
        duration = time() - self._timings[name]
        del self._timings[name]
        self.logger.info("end {}: {} seconds".format(name, duration))

    def _get_configuration(self, key):
        """
        Get the configuration for a command.
        Parameters
        ----------
        key : str
            the command to get the configuration for
        """
        # Empty values
        if key not in self.configuration:
            return {}

        # Get the configuration recursively
        if isinstance(self.configuration[key], basestring):
            configuration = self._get_configuration(self.configuration[key])
        else:
            configuration = self.configuration[key]

        # Check type
        if not isinstance(configuration, dict):
            msg = "configuration for '{}' must be a dictionary".format(key)
            self.logger.critical(msg)
            raise ValueError(msg)

        return configuration

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
            recursive_update(configuration, json_loads(text))
            configuration_hash = hashlib.sha256(text).hexdigest()
        except IOError as ex:
            self.logger.critical(ex.message)
            raise

        return configuration, configuration_hash

    def _format_path(self, p):
        if p.startswith('?/'):
            return path.join(path.dirname(self.arguments.configuration_file), p[2:])
        return p

    def _load_result(self, repeat=None):
        """
        Load the previous result file and ensure the configuration matches.
        """
        result_file = self._get_result_file(repeat)

        if path.exists(result_file):
            self.logger.info("loading results from '{}'".format(result_file))
            result = json_load(result_file)

            if result['configuration']['hash'] != self.configuration_hash:
                self.logger.info('configuration hash mismatch; deleting previous results')
                result = {}
        else:
            result = {}

        result['configuration'] = {
            'hash': self.configuration_hash,
            'path': path.abspath(self.arguments.configuration_file),
        }

        return result

    def _get_result_file(self, repeat=None):
        # Get the result file
        result_file = self.arguments.out or self.configuration.get('result_file', None)
        # Check everything is ok
        if not result_file:
            msg = "'result_file' must be specified in the configuration or command line"
            self.logger.critical(msg)
            raise ValueError(msg)

        # Nothing else to do if we aren't repeating the analysis
        if repeat is None:
            return self._format_path(result_file)

        # Replace the placeholder with the repetition number
        assert '$' in result_file, "'result_file' must contain $ placeholder if `repeat` is set"
        return self._format_path(result_file.replace('$', str(repeat)))

    def _get_repeat(self):
        return self.arguments.repeat or self.configuration.get('repeat', None)

    def _dump_result(self, repeat=None):
        """
        Dump the result of the pipeline to disk.
        """
        # Ensure the directory exists
        result_file = self._get_result_file(repeat)

        dirname = path.dirname(result_file)
        if dirname:
            mkdir_p(dirname)
        # Dump the results to disk
        self.logger.info("dumping results to '{}'".format(result_file))
        json_dump(self.result, result_file, indent=2)

    def run(self):
        """
        Run the pipeline.
        """
        # Get the arguments
        self.arguments = self.argument_parser.parse_args()
        # Set up logging
        self.logger.setLevel({'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING,
                              'error': logging.ERROR, 'critical': logging.CRITICAL}[self.arguments.level])
        self.logger.addHandler(logging.StreamHandler(stdout))
        self.logger.info('{} {}'.format(self.name, vars(self.arguments)))
        # Load the configuration
        self.configuration, self.configuration_hash = self._load_configuration()

        repeat = self._get_repeat()
        for i in range(repeat or 1):
            # Get previous results
            self.result = self._load_result(None if repeat is None else i)
            # Iterate over all commands and execute them
            for command in self.arguments.commands:
                self._begin(command)
                self._evaluate(command)
                self._end(command)

            self._dump_result(None if repeat is None else i)
            # Clear results
            self.result = {}
            self._reset()

        self.logger.info('Exit')

    def _reset(self):
        """
        Reset the pipeline between repetitions.
        """
        pass

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
            return self.result[command]
        else:
            self.logger.info("begin command '{}'".format(command))

        # Execute the command
        fun, args = self._commands[command]
        result = fun(self._get_configuration(command), *args)

        self.logger.info("end command '{}'".format(command))
        # Store the result
        if result is not None:
            self.result[command] = result
        return result

    def show(self, _):
        self.logger.info(json_dumps(self.result, cls=StringEncoder, indent=4))

    @property
    def _commands(self):
        """
        Get a dictionary of command names and implementations.
        """
        return {
            'show': (self.show, [])
        }
