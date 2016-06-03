from .util import json_load, json_dump, mkdir_p, json_dumps, StringEncoder, Timer
from argparse import ArgumentParser, Action
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm, trange
from os import path
from sys import argv


class ValidateChoices(Action):
    """
    Action to validate multiple choices.
    """
    def __call__(self, parser, args, values, option_string=None):
        for item in values:
            assert item in self.metavar, "'{}' is not a recognised command".format(item)
        setattr(args, self.dest, values)


class Pipeline(object):
    """
    Abstract base class for pipelines.

    Individual commands should be implemented as instance methods starting with `run_` and should return a value that
    evaluates to `True` after a boolean cast to support caching.
    """
    def __init__(self, output_file=None, seed=None, verbose=True, force=False):
        self.commands = None
        self.seed = seed
        self.verbose = verbose
        self.output_file = output_file
        self.result = None
        self.force = force

    def setup(self):
        if self.output_file and path.exists(self.output_file):
            self.result = json_load(self.output_file)
        else:
            self.result = {}

    @property
    def available_commands(self):
        """
        Get the commands supported by the example.
        """
        return {name[4:]: getattr(self, name) for name in dir(self) if name.startswith('run_')}

    def init_argument_parser(self):
        """
        Initialise the argument parser. Inheriting classes can override this function to add additional parameters.
        """
        parser = ArgumentParser()
        # Add optional arguments
        if self.output_file:
            output_file = self.output_file
        elif argv[0]:
            output_file, _ = path.splitext(path.abspath(argv[0]))
            output_file = output_file + '.json'
        else:
            output_file = None

        parser.add_argument('--output_file', '-o', type=str, help="output file", default=output_file)
        parser.add_argument('--seed', '-s', type=int, help="random number generator seed", default=self.seed)
        parser.add_argument('--force', '-f', action='store_true', help="force reexecution of all commands",
                            default=self.force)
        parser.add_argument('commands', nargs='*', help="commands to execute", action=ValidateChoices,
                            metavar=self.available_commands.keys())
        return parser

    def parse_args(self):
        """
        Parse the command line arguments.

        Parameters
        ----------
        kwargs : dict
            key value pairs of default parameter values

        Returns
        -------
        args : NameSpace
            parsed command line arguments
        """
        parser = self.init_argument_parser()
        # Parse arguments
        args = parser.parse_args()
        # Update attributes
        self.__dict__.update(vars(args))

    def run(self):
        """
        Run the examples specified by the command line arguments.
        """
        if self.commands is None:
            self.parse_args()

        # Get the specified commands or all commands
        commands = self.commands or self.available_commands

        # Setup
        self.setup()

        # Run the commands
        for command in commands:
            np.random.seed(self.seed)
            self.require(command)

        # Save the results
        self.save_result()

        # Show any figures that were produced
        plt.show()

    def require(self, command):
        """
        Execute a command if it has not yet been evaluated or `force` is true.

        Parameters
        ----------
        command : str
            command to execute

        Returns
        -------
        result : object
            value returned by the command
        """
        if command not in self.result or not self.result[command] or self.force:
            self.write("========== Start    {} ==========", command)
            with Timer(logger=None) as timer:
                self.result[command] = self.available_commands[command]()
            self.write("========== Executed {} in {:.3f} seconds ==========", command, timer.duration)

        else:
            self.write("========== Cached   {} ==========", command)

        return self.result[command]

    def save_result(self, output_file=None):
        """
        Save the results to a file.

        Parameters
        ----------
        output_file : str or None
            filename of the output file or `None` to use `self.output_file`
        """
        output_file = output_file or self.output_file
        if output_file:
            mkdir_p(output_file)
            json_dump(self.result, output_file)
        else:
            raise ValueError('cannot save results because `output_file` was not specified')

    def range(self, *args):
        """
        `tqdm.trange` if `verbose` is `True` else `range`.

        Parameters
        ----------
        args : list
            arguments passed to `tqdm.trange` or `range`

        Returns
        -------

        """
        if self.verbose:
            return trange(*args)
        else:
            return range(*args)

    def write(self, message, *args, **kwargs):
        """
        Write a message using `tqdm` if `verbose` is `True`.

        Parameters
        ----------
        message : object
        args : list
        kwargs : dict
        """
        message = str(message).format(*args, **kwargs)

        if self.verbose and hasattr(tqdm, '_instances'):
            tqdm.write(message)
        elif self.verbose:
            print message

    def run_show(self):
        """
        Show the results formatted as JSON.
        """
        text = json_dumps(self.result, cls=StringEncoder)
        print text
        # Do not support caching
        return None



'''
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
    def __init__(self, name, **configuration):
        self.name = name
        # Get the configuration
        self.configuration = recursive_update(self._default_configuration(), configuration)
        self.arguments = None
        self.result = None

        # Set up the argument parser
        self.argument_parser = ArgumentParser(name)
        self.argument_parser.add_argument('--force', '-f', help='reevaluate all commands', action='store_true',
                                          default=False)
        self.argument_parser.add_argument('--out', '-o', help="override output filename", type=str)
        self.argument_parser.add_argument('--level', '-l', help='logging level', default='info',
                                          choices=['debug', 'info', 'warning', 'error', 'critical'])
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
        else:
            self.logger.info("creating new result set for '{}'".format(result_file))
            result = {}

        # Set the configuration for reference
        result['configuration'] = self.configuration

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

        repeat = self.configuration.get('repeat', None)
        for i in range(repeat or 1):
            # Get previous results
            self.result = self._load_result(None if repeat is None else i)
            # Iterate over all commands and execute them
            for command in self.arguments.commands:
                self._begin(command)
                self._execute(command)
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

    def _execute(self, command):
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
'''