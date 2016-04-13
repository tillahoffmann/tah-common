from matplotlib import pyplot as plt
import numpy as np
from tah_common.sampling import HamiltonianSampler
from example_base import normal_log_posterior, normal_log_posterior_jac

np.random.seed(1)

mean = np.asarray([-1, 1, 3])
variance = np.asarray([.1, 1, 10])
parameter_names = [r'$\mu_{{{0}}}$'.format(i + 1) for i in range(len(mean))]

# Initialise the adaptive metropolis sampler
mass = 1.0 / variance
sampler = HamiltonianSampler(normal_log_posterior, (mean, variance), parameter_names, jac=normal_log_posterior_jac, mass=mass)
# Obtain 2000 samples
sampler.sample(mean, 2000)

# Test the dynamics
sampler.dynamics_plot(sampler.samples[-1], .02, 400)

burn_in = 500
sampler.describe(burn_in)
sampler.trace_plot(burn_in)
sampler.grid_density_plot(burn_in)

plt.show()