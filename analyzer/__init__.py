# Licensed under the MIT License - see LICENSE.txt
""" Loganalyzer: A Python package for log analyzing.

* Code: Link TBD
* Docs: Link TBD

The top-level `analyzer` namespace is almost empty,
it only contains this:

::

 __version__        --- Loganalyzer version string

The Loganalyzer functionality is available by importing from
the following sub-packages (e.g. `analyzer.parser`):

::

 config             --- Global config file
 preprocess         --- Preprocess raw logs before parsing them
 parser             --- Clustering, generate templates
 oldschool          --- Anomaly detection (Knowledge-base)
 modern.loglizer    --- Anomaly detection (Calssical ML)
 modern.deeplog     --- Anomaly detection (Deep Learning)
 modern.loglab      --- Anomaly multi-classification
 utils              --- Utility functions and classes
"""

__all__ = ["__version__"]

import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    # Package is not installed, so use hard-coded version instead
    __version__ = "2.0.0"
