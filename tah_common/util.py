import numpy as np
import json, base64
import errno
from os import makedirs, path
import functools
from time import time
import logging


def autospace(x, num=50, mode='lin', factor=0.1):
    """
    Get a vector with equal spacing whose range is determined by `x`.

    Parameters
    ----------
    x : array_like
        vector to use for range determination
    num : int
        number of sample points
    mode : str
        'lin' for linear spacing, 'log' for log spacing
    factor : float
        factor by which to extend the range
    """
    if mode == 'log':
        x = np.log(x)

    # Evaluate the range
    xmin = np.min(x)
    xmax = np.max(x)
    xrng = xmax - xmin

    # Create the samples
    y = np.linspace(xmin - factor * xrng, xmax + factor * xrng, num)

    # Transform samples
    if mode == 'log':
        return np.exp(y)
    elif mode == 'lin':
        return y
    else:
        raise KeyError(mode)


def haversine(pos1, pos2, degree=True):
    """
    Calculate the great circle distance between two points on the earth in km.

    Parameters
    ----------
    pos1 : tuple
        tuple of latitude and longitude coordinates
    pos2 : tuple
        tuple of latitude and longitude coordinates
    degree : bool
        whether the coordinates are in degree or radians
    """
    lat1, lon1 = pos1
    lat2, lon2 = pos2
    # Convert decimal degrees to radians
    if degree:
        lon1, lat1, lon2, lat2 = np.deg2rad([lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371
    return c * r


class NumpyEncoder(json.JSONEncoder):
    """
    JSON encoder that supports numpy arrays.

    References
    ----------
    http://stackoverflow.com/a/24375113/1150961
    """
    def default(self, obj):
        """
        If input object is an ndarray it will be converted into a dict holding
        dtype, shape and the data, base64 encoded.

        Parameters
        ----------
        obj : object
            value to encode
        """
        if isinstance(obj, np.ndarray):
            if obj.flags['C_CONTIGUOUS']:
                obj_data = obj.data
            else:
                cont_obj = np.ascontiguousarray(obj)
                assert(cont_obj.flags['C_CONTIGUOUS'])
                obj_data = cont_obj.data
            data_b64 = base64.b64encode(obj_data)
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder(self, obj)


class StringEncoder(json.JSONEncoder):
    """
    JSON encoder that encodes unsupported types as strings.
    """
    def default(self, obj):
        try:
            return super(StringEncoder, self).default(obj)
        except TypeError:
            return repr(obj)


def json_numpy_obj_hook(dictionary):
    """
    Decodes a previously encoded numpy ndarray with proper shape and dtype.

    Parameters
    ----------
    dictionary : dict
        json encoded ndarray

    References
    ----------
    http://stackoverflow.com/a/24375113/1150961
    """
    if isinstance(dictionary, dict) and '__ndarray__' in dictionary:
        data = base64.b64decode(dictionary['__ndarray__'])
        return np.frombuffer(data, dictionary['dtype']).reshape(dictionary['shape'])
    # Return the original data if we cannot decode
    return dictionary


def json_load(f, encoding=None, cls=None, object_hook=None, parse_float=None, parse_int=None, parse_constant=None,
              object_pairs_hook=None, **kwargs):
    """
    Convenience function to load JSON.

    Parameters
    ----------
    f : str or file
        file pointer or file name to read from

    Notes
    -----
    See json.load for details of the other parameters.
    """
    # Open a file if a string is given
    if isinstance(f, basestring):
        fp = open(f)
    elif isinstance(f, file):
        fp = f
    else:
        raise ValueError('`f` must be a file pointer or file name')

    # Load the data
    result = json.load(fp, encoding, cls, object_hook or json_numpy_obj_hook, parse_float, parse_int, parse_constant,
                       object_pairs_hook, **kwargs)

    # Close the file if we just opened it
    if isinstance(f, str):
        fp.close()

    return result


def json_loads(s, encoding=None, cls=None, object_hook=None, parse_float=None, parse_int=None, parse_constant=None,
               object_pairs_hook=None, **kwargs):
    """
    Convenience function to load JSON from a string.

    Notes
    -----
    See json.loads for details of the parameters.
    """
    return json.loads(s, encoding, cls, object_hook or json_numpy_obj_hook, parse_float, parse_int, parse_constant,
                      object_pairs_hook, **kwargs)


def json_dump(obj, f, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=None,
              separators=None, encoding='utf-8', default=None, sort_keys=False, **kwargs):
    """
    Convenience function to dump JSON.

    Parameters
    ----------
    f : str or file
        file pointer or file name to write to

    Notes
    -----
    See json.dump for details of the other parameters.
    """
    if isinstance(f, basestring):
        fp = open(f, 'w')
    elif isinstance(f, file):
        fp = f
    else:
        raise ValueError("`f` must be a file pointer or file name but got '{}'".format(f))

    # Load the data
    result = json.dump(obj, fp, skipkeys, ensure_ascii, check_circular, allow_nan, cls or NumpyEncoder, indent,
                       separators, encoding, default, sort_keys, **kwargs)

    # Close the file if we just opened it
    if isinstance(f, str):
        fp.close()


def json_dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=None,
              separators=None, encoding='utf-8', default=None, sort_keys=False, **kwargs):
    """
    Convenience function to dump JSON to a string.

    Notes
    -----
    See json.dumps for details of the parameters.
    """
    return json.dumps(obj, skipkeys, ensure_ascii, check_circular, allow_nan, cls or NumpyEncoder, indent,
                       separators, encoding, default, sort_keys, **kwargs)


def read(filename):
    """
    Read all text from the specified file.

    Parameters
    ----------
    filename : str
        path to read from
    """
    with open(filename) as fp:
        return fp.read()


def recursive_update(self, other):
    """
    Update dictionary recursively.

    Parameters
    ----------
    self : dict
        dictionary to update
    other : dict
        dictionary to copy values from
    """
    for key, value in other.iteritems():
        # Simply copy the values if the value is not in the original dictionary or if we aren't dealing with dicts
        if key not in self or not isinstance(value, dict) or not isinstance(self[key], dict):
            self[key] = value
        # Perform a recursive update otherwise
        else:
            recursive_update(self[key], value)

    return self


def mkdir_p(p):
    """
    Create a directory if it does not exist.

    Parameters
    ----------
    p : str
        the directory to create
    """
    try:
        makedirs(p)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and path.isdir(p):
            pass
        else:
            raise


class timeit:
    """
    Time the execution of a function and log the results.

    Parameters
    ----------
    logger : str
        name of the logger
    level : str
        logging level for the reporting
    """
    def __init__(self, logger=None, level='debug'):
        self.logger = logging.getLogger('tah_common.util' if logger is None else logger)
        self.level = level.lower()

    def __call__(self, func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            # Call the function
            begin = time()
            result = func(*args, **kwargs)
            end = time()
            duration = end - begin
            # Report the time
            getattr(self.logger, self.level)("%s: %s", func.func_name, str(duration))
            return result

        return inner


