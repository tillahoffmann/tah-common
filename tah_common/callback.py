import logging


class CallbackChain(object):
    """
    Chain together callbacks.
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        if 'return_value' in kwargs:
            self.return_value = kwargs['return_value']

    def __call__(self, *args, **kwargs):
        result = None
        for arg in self.args:
            result = arg(*args, **kwargs)

        return getattr(self, 'return_value', result)


class PeriodicCallback(object):
    """
    Callback that is only executed every `n` times.
    """
    def __init__(self, callback, period=1):
        self.period = period
        self.callback = callback
        self.current = 0

    def __call__(self, *args, **kwargs):
        if not self.period:
            return

        if self.current < self.period:
            self.current += 1
        else:
            self.current = 0
            return self.callback(*args, **kwargs)


class LoggingCallback(object):
    """
    Callback that logs its arguments.
    """
    def __init__(self, logger=None, level='info', format=None):
        self.logger = logger if isinstance(logger, logging.Logger) else logging.getLogger(logger)
        self.format = format or "{name}: {{args}}, {{kwargs}}".format(name=self.logger.name)
        self.level = level.lower()

    def __call__(self, *args, **kwargs):
        if not hasattr(self.logger, self.level):
            raise KeyError(self.level)

        method = getattr(self.logger, self.level)
        return method(self.format.format(args=args, kwargs=kwargs))

