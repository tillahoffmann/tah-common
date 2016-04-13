import numpy as np
from ..plot import trace_plot, density_plot
import pandas as pd


class ReportCallback(object):
    """
    Callback that reports its argument and can be chained with other callbacks.

    Parameters
    ----------
    period : int
        how often to report
    *others : list
        other callbacks to execute
    """
    def __init__(self, period, format=None, *others):
        self.period = period
        self.format = format or "Iteration: {}; Parameters: {}"
        self.current = 0
        self.others = others

    def __call__(self, parameters):
        self.current += 1
        if self.period and self.current % self.period == 0:
            print self.format.format(self.current, parameters)
        # Call all the other callbacks
        for other in self.others:
            other(parameters)


class BaseSampler(object):
    """
    Base class for MCMC samplers.

    Parameters
    ----------
    fun : callable
        log-posterior or log-likelihood function taking a vector of parameters as its first argument
    args : array_like
        additional arguments to pass to `fun`
    parameter_names : list
        list of parameter names
    break_on_interrupt : bool
        stop the sampler rather than throwing an exception upon a keyboard interrupt
    """
    def __init__(self, fun, args=None, parameter_names=None, break_on_interrupt=True):
        if not callable(fun):
            raise ValueError("`fun` must be callable")

        self.fun = fun
        self.args = [] if args is None else args
        self.parameter_names = parameter_names
        self.break_on_interrupt = break_on_interrupt

        self._samples = []
        self._fun_values = []

    def get_parameter_name(self, index):
        """
        Get a parameter name.

        Parameters
        ----------
        index : int
            index of the parameter for which to get a name
        """
        return str(index) if self.parameter_names is None else self.parameter_names[index]

    def trace_plot(self, burn_in=0, parameters=None, values=None):
        """
        Plot the trace of parameters (and horizontal lines indicating the true values).

        Parameters
        ----------
        burn_in : int
            number of initial values to discard
        parameters : iterable
            indices of the parameters to plot (default is all)
        values : iterable
            true values corresponding to the indices in `parameters`
        """
        return trace_plot(self.samples, self.fun_values, burn_in, None if parameters is None else
            {p: self.get_parameter_name(p) for p in parameters}, values)

    def density_plot(self, burn_in=0, parameters=None, values=None, nrows=None, ncols=None, bins=10):
        """
        Plot the marginal densities of parameters  (and vertical lines indicating the true values).

        Parameters
        ----------
        burn_in : int
            number of initial values to discard
        parameters : iterable
            indices of the parameters to plot (default is all)
        values : iterable
            true values corresponding to the indices in `parameters`
        nrows : int
            number of rows in the plot
        ncols : int
            number of columns in the plot
        bins : int
            number of bins for the histograms
        """
        return density_plot(self.samples, burn_in, None if parameters is None else
            {p: self.get_parameter_name(p) for p in parameters}, values, nrows, ncols, bins)

    def acceptance_rate(self, burn_in=0):
        """
        Evaluate the acceptance rate.

        Parameters
        ----------
        burn_in : int
            number of initial values to discard
        """
        samples = self.samples[burn_in:]
        return np.mean(samples[1:] != samples[:-1])

    def sample(self, parameters, steps=1, callback=None):
        """
        Draw samples from the distribution.

        Parameters
        ----------
        parameters : array_like
            current state of the chain
        steps : int
            number of steps
        callback : callable
            callback after each step
        """
        raise NotImplementedError

    def describe(self, burn_in=0, parameters=None, do_print=True):
        """
        Get a description of the parameters.

        Parameters
        ----------
        burn_in : int
            number of initial values to discard
        parameters : iterable
            indices of the parameters to plot (default is all)
        do_print : bool
            whether to print the description
        """
        if parameters is None:
            parameters = np.arange(self.samples.shape[1])

        # Use pandas to get a description
        columns = map(self.get_parameter_name, parameters)
        frame = pd.DataFrame(self.samples[burn_in:, parameters], columns=columns)
        description = frame.describe()

        name = self.__class__.__name__

        description = "{}\n{}\n{}".format(name, '=' * len(name), description)

        if do_print:
            print description

        return description

    @property
    def samples(self):
        """
        Get the samples.
        """
        return np.asarray(self._samples)

    @property
    def fun_values(self):
        """
        Get the function values.
        """
        return np.asarray(self._fun_values)
