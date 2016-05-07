from matplotlib import pyplot as plt
import numpy as np
from tah_common.plotting import get_style
from tah_common.util import mkdir_p
from os import path
from sys import argv


def create_plot(style):
    """
    Create a plot based on http://matplotlib.org/examples/style_sheets/plot_ggplot.html.
    """
    with plt.style.context(get_style(style)):
        # Set a seed for consistent plots
        np.random.seed(1)

        fig, axes = plt.subplots(ncols=2, nrows=2)
        ax1, ax2, ax3, ax4 = axes.ravel()

        # scatter plot (Note: `plt.scatter` doesn't use default colors)
        x, y = np.random.normal(size=(2, 200))
        ax1.plot(x, y, 'o')

        # sinusoidal lines with colors from default color cycle
        L = 2 * np.pi
        x = np.linspace(0, L)
        ncolors = len(plt.rcParams['axes.color_cycle'])
        shift = np.linspace(0, L, ncolors, endpoint=False)
        for s in shift:
            ax2.plot(x, np.sin(x + s), '-')

        # bar graphs
        x = np.arange(5)
        y1, y2 = np.random.randint(1, 25, size=(2, 5))
        width = 0.25
        ax3.bar(x, y1, width)
        ax3.bar(x + width, y2, width, color=plt.rcParams['axes.color_cycle'][2])
        ax3.set_xticks(x + width)
        ax3.set_xticklabels(['a', 'b', 'c', 'd', 'e'])

        # circles with colors from default color cycle
        for i, color in enumerate(plt.rcParams['axes.color_cycle']):
            xy = np.random.normal(size=2)
            ax4.add_patch(plt.Circle(xy, radius=0.3, color=color))
        ax4.axis('equal')

        fig.suptitle(style)
        fig.tight_layout()

    return fig

# Get the styles
if len(argv) > 1:
    styles = argv[1:]
else:
    styles = ['koma'] + plt.style.available

# iterate over all styles and create figures
for style in styles:
    print style,
    fig = create_plot(style)

    # Save the figures
    for ext in ['ps', 'pdf', 'png']:
        dirname = 'styles_figures/{}'.format(ext)
        mkdir_p(dirname)
        fig.savefig(path.join(dirname, '{}.{}'.format(style, ext)))
        print ext,

    plt.close(fig)
    print

