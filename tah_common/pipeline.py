from .util import json_load, json_dump, mkdir_p, json_dumps, StringEncoder, Timer
from argparse import ArgumentParser, Action
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm
from os import path
from sys import argv, stdout
import logging
import functools
import hashlib


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

    Individual commands should be implemented as instance methods starting with `run_` and should return a falsy value
    to not be cached on disk.
    """
    def __init__(self, output_file=None, seed=None, logger=True):
        self.commands = None
        self.seed = seed
        self.output_file = output_file
        self.result = {}

        # Set up loggers
        if isinstance(logger, str):
            self.logger = logging.getLogger(logging)
        elif logger:
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(stdout)
            self.logger.addHandler(handler)
        else:
            self.logger = None

        self.parser = ArgumentParser(argv[0])
        self.arguments = []

    def add_argument(self, name, *args, **kwargs):
        name = name.strip('-')
        if 'default' not in kwargs:
            kwargs['default'] = getattr(self, name)
        self.parser.add_argument('--' + name, *args, **kwargs)
        self.arguments.append(name)

    @property
    def configuration(self):
        return {argument: getattr(self, argument) for argument in self.arguments}

    def log(self, level, message, *args, **kwargs):
        if self.logger:
            message = str(message).format(*args, **kwargs)
            self.logger.log(level, message)

    def info(self, message, *args, **kwargs):
        self.log(logging.INFO, message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        self.log(logging.WARN, message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        self.log(logging.DEBUG, message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.log(logging.CRITICAL, message, *args, **kwargs)

    def setup(self):
        """
        Set up the pipeline and load results.
        """
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
        # Add all the positional arguments directly (they shouldn't be part of the configuration)
        self.parser.add_argument('commands', nargs='*', help="commands to execute", action=ValidateChoices,
                                 metavar=self.available_commands.keys())

        self.add_argument('--output_file', '-o', type=str, help="output file", default=self.output_file)
        self.add_argument('--seed', '-s', type=int, help="random number generator seed", default=self.seed)

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
        self.init_argument_parser()
        # Parse arguments
        args = self.parser.parse_args()
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

        if not self.output_file and argv and argv[0]:
            # Get the name of the script
            script = path.split(argv[0])[-1]
            basename = path.splitext(script)[0]
            # Create a hash of the configuration
            self.output_file = "{}_{}.json".format(basename, hashlib.md5(repr(self.configuration)).hexdigest())

        # Setup
        self.setup()

        # Run the commands
        for command in commands:
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
        result : any
            value returned by the command
        """
        if command not in self.result:
            self.info("========== Start    {} ==========", command)
            # Set the seed before each execution
            np.random.seed(self.seed)
            with Timer(logger=None) as timer:
                self.result[command] = self.available_commands[command]()
            self.info("========== Executed {} in {:.3f} seconds ==========", command, timer.duration)

        else:
            self.info("========== Cached   {} ==========", command)

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
        if not output_file:
            raise ValueError('cannot save results because `output_file` was not specified')

        mkdir_p(output_file)
        result = {key: value for key, value in self.result.iteritems() if value}
        result['configuration'] = self.configuration
        json_dump(result, output_file, indent=4)

    def run_show(self):
        """
        Show the results formatted as JSON.
        """
        text = json_dumps(self.result, cls=StringEncoder, indent=4)
        print text

    @functools.wraps(tqdm)
    def tqdm(self, *args, **kwargs):
        if 'disable' not in kwargs:
            kwargs['disable'] = self.logger is None
        return tqdm(*args, **kwargs)
