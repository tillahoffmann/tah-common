from matplotlib import pyplot as plt
import numpy as np
from tah_common.sampling import AdaptiveMetropolisSampler
from example_base import normal_log_posterior

np.random.seed(1)

mean = np.asarray([-1, 1, 3])
parameter_names = [r'$\mu_{{{0}}}$'.format(i + 1) for i in range(len(mean))]

# Initialise the adaptive metropolis sampler
sampler = AdaptiveMetropolisSampler(normal_log_posterior, (mean,), parameter_names)
# Obtain 2000 samples
sampler.sample(mean, 2000)

sampler.describe()
sampler.trace_plot()
sampler.density_plot()

plt.show()