def normal_log_posterior(parameters, mean=0, variance=1):
    return -0.5 * np.sum((parameters - mean) ** 2 / variance)


def normal_log_posterior_jac(parameters, mean=0, variance=1):
    return - (parameters - mean) / variance