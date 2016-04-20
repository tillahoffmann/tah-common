import numpy as np


def normal_log_posterior(parameters, mean=0, variance=1):
    return -0.5 * np.sum((parameters - mean) ** 2 / variance)


def normal_log_posterior_jac(parameters, mean=0, variance=1):
    return - (parameters - mean) / variance


if __name__ == '__main__':
    print "{} provides helper functions for other examples but cannot be run independently".format(__file__)