# Licensed under the MIT License - see License.txt
""" Loganalyzer: A Python package for log analyzing.

* Code: Link TBD
* Docs: Link TBD

The top-level `analyzer` namespace is almost empty,
it only contains this:

::

 __version__       --- Loganalyzer version string

The Loganalyzer functionality is available by importing from
the following sub-packages (e.g. `analyzer.parser`):

::

 config            --- Global config file
 preprocess        --- Preprocess raw logs before parsing them
 parser            --- Clustering, generate templates
 loglizer          --- Anomaly detection (Calssical ML)
 deeplog           --- Anomaly detection (Deep Learning)
 oldschool         --- Anomaly detection (Knowledge-base)
 loglab            --- Anomaly multi-classification
 utils             --- Utility functions and classes
"""

__all__ = ["__version__"]
# __version__ = "1.0.0"

import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    # package is not installed
    pass
