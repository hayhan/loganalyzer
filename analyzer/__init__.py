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

 preprocessor      --- Preprocess raw logs before parsing them
 parser            --- Clustering, templates extracting
 classifier        --- Log classifying
 postprocessor     --- Postprocess results
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
