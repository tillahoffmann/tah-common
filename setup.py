from setuptools import setup
from os import path


def read(fn):
    dir = path.dirname('__file__')
    with open(path.join(dir, fn)) as fp:
        return fp.read()

setup(
    name='tah_common',
    version=read('VERSION'),
    author='Till Hoffmann',
    author_email='tillahoffmann@gmail.com',
    description='commonly used functionality',
    long_description=read('README.md'),
    url='https://github.com/tillahoffmann/tah_common',
    packages=['tah_common'],
    requires=[
        'numpy',
        'scipy',
        'matplotlib',
        'pandas',
    ]
)
