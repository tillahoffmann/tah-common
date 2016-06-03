from matplotlib import pyplot as plt
from matplotlib import rcParams, rcParamsDefault
import numpy as np
import itertools as it
from scipy.stats import gaussian_kde
from .util import autospace
from os import path


def kde_plot(x, ax=None, **kwargs):
    """
    Plot a univariate kernel density estimate.

    Parameters
    ----------
    x : array_like
        values to plot
    ax : Axes
        axes to plot into
    kwargs : dict
        additional keyword arguments passed to `ax.plot`
    """
    ax = ax or plt.gca()
    kde = gaussian_kde(x)
    linx = autospace(x)
    y = kde(linx)
    ax.plot(linx, y, **kwargs)


def density_plot(samples, burn_in=0, name=None, value=None, bins=10, ax=None):
    """
    Plot the density of a parameter (and a vertical indicating the true value).

    Parameters
    ----------
    samples : array_like
        samples of the parameters
    burn_in : int
        number of initial values to discard
    name : str
        name of the parameter
    value : float
        true value
    bins : int
        number of bins for the histogram
    ax : Axes
        axes to plot into
    """
    ax = ax or plt.gca()
    x = samples[burn_in:]

    # Create a histogram
    ax.hist(x, bins, normed=True, histtype='stepfilled', facecolor='silver')

    # Plot the kde
    kde_plot(x, ax, color='blue')
    ax.set_title(name)

    # Plot true values
    if value is not None:
        ax.axvline(value, ls='dotted')


def grid_density_plot(samples, burn_in=0, parameters=None, values=None, nrows=None, ncols=None, bins=10):
    """
    Plot the marginal densities of parameters  (and vertical lines indicating the true values).

    Parameters
    ----------
    samples : array_like
        samples of the parameters
    burn_in : int
        number of initial values to discard
    parameters : dictionary
        indices of the parameters to plot as keys and names as values (default is all)
    values : iterable
        true values corresponding to the indices in `parameters`
    nrows : int
        number of rows in the plot
    ncols : int
        number of columns in the plot
    bins : int
        number of bins for the histograms
    """
    if parameters is None:
        parameters = {i: str(i) for i in np.arange(samples.shape[1])}
    if values is None:
        values = []

    # Determine the number of rows and columns if not specified
    n = len(parameters)
    if nrows is None and ncols is None:
        ncols = int(np.ceil(np.sqrt(n)))
        nrows = int(np.ceil(float(n) / ncols))
    elif nrows is None:
        nrows = int(np.ceil(float(n) / ncols))
    elif ncols is None:
        ncols = int(np.ceil(float(n) / nrows))

    fig, axes = plt.subplots(nrows, ncols)

    # Plot all parameters
    for ax, parameter, value in it.izip_longest(np.ravel(axes), parameters, values, fillvalue=None):
        # Skip if we have run out of parameters
        if parameter is None:
            break

        # Plot the individual density estimate
        density_plot(samples[:, parameter], burn_in, parameters[parameter], value, bins, ax)


    fig.tight_layout()

    return fig, axes


def trace_plot(samples, fun_values, burn_in=0, parameters=None, values=None):
    """
    Plot the trace of parameters (and horizontal lines indicating the true values).

    Parameters
    ----------
    samples : array_like
        samples of the parameters
    fun_values : array_like
        values of the objective function
    burn_in : int
        number of initial values to discard
    parameters : iterable
        indices of the parameters to plot (default is all)
    values : iterable
        true values corresponding to the indices in `parameters`
    """

    if parameters is None:
        parameters = {i: str(i) for i in range(samples.shape[1])}
    if values is None:
        values = []

    fig, (ax1, ax2) = plt.subplots(1, 2, True)

    # Plot the trace
    for parameter, value in it.izip_longest(parameters, values, fillvalue=None):
        line, = ax1.plot(samples[burn_in:, parameter], label=parameters[parameter])
        # Plot the true values
        if value is not None:
            ax1.axhline(value, ls='dotted', color=line.get_color())

    ax1.set_xlabel('Iterations')
    ax1.set_ylabel('Parameter values')
    ax1.legend(loc=0, frameon=False)

    ax2.plot(fun_values[burn_in:])
    ax2.set_xlabel('Iterations')
    ax2.set_ylabel('Function values')

    fig.tight_layout()

    return fig, (ax1, ax2)


def get_style(style):
    """
    Get matplotlib style specification.

    Parameters
    ----------
    style : str
        name of the style
    """
    # Use the default style or load it if it is available
    if style in plt.style.available or path.exists(style) or style == 'default':
        return style

    # Construct a filename in the package
    filename = path.join(path.dirname(path.realpath(__file__)), 'stylelib', style + '.mplstyle')
    if path.exists(filename):
        return filename

    raise ValueError("could not locate style specification '{}'".format(style))


def savefigs(fig, filename, *formats, **kwargs):
    """
    Save a figure in multiple formats.

    Parameters
    ----------
    fig : Figure
    filename : str
    formats : list
    """
    if formats:
        # Get the base name without extension
        basename, ext = path.splitext(filename)
        if ext:
            formats = (ext,) + formats
        # Iterate over all formats
        for format in formats:
            # Prepend a dot if necessary
            if not format.startswith('.'):
                format = '.' + format
            # Save the file
            fig.savefig(basename + format, **kwargs)
    else:
        fig.savefig(filename, **kwargs)