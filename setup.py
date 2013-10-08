import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="ipycache",
    version="0.1.2dev",
    author="Cyrille Rossant",
    author_email="rossant@github",
    description=(("Defines a %%cache cell magic in the IPython notebook to "
                   "cache results of long-lasting computations in a persistent"
                   "pickle file.")),
    license="BSD",
    keywords="ipython notebook cache",
    url="http://packages.python.org/ipycache",
    py_modules=['ipycache'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Framework :: IPython",
        "License :: OSI Approved :: BSD License",
    ],
)

