Install & Run
=============

Dependency
----------

::

 - python >= 3.6
 - numpy
 - scipy
 - scikit-learn
 - pandas
 - matplotlib
 - tqdm
 - click
 - pyyaml
 - skl2onnx
 - onnxruntime
 - sphinx
 - pytest
 - pytest-benchmark
 - umap-learn
 - pytorch >= 1.5.0

Installation
------------

::

 At the top directory of loganalyzer clone, run commands below
 (pay attention to the dot) to install the analyzer package. Then
 export environment var ANALYZER_DATA. Also, extract raw.7z in
 data. Now you can use the "analyzer" command. Type "analyzer --help"
 for sub commands and options.

 $ pip install .

 [Linux or macOS]
 $ export ANALYZER_DATA=path_to_your_clone_dir/data

 [Windows PowerShell]
 C:\> $env:ANALYZER_DATA="path_to_your_clone_dir\data"

 To get api documents of html format, run commands below in docs
 directory of your clone. The generated html pages are under
 docs/build/html/.

 [Linux or macOS]
 $ sphinx-apidoc -f -o source ../analyzer && make html

 [Windows PowerShell]
 C:\> sphinx-apidoc -f -o source ..\analyzer; .\make.bat html

Command line interface
----------------------

::

 $ analyzer
 Usage: analyzer [OPTIONS] COMMAND [ARGS]...

   Loganalyzer command line interface (CLI).

   Loganalyzer is a Python package for log analyzing.

   Use ``--help`` to see available sub-commands, as well as the available
   arguments and options for each sub-command.

 Examples:

   $ analyzer --help
   $ analyzer --version
   $ analyzer info --help
   $ analyzer info

 Options:

   --log-level [debug|info|warning|error]
                                   Logging verbosity level.
   --ignore-warnings               Ignore warnings.
   --version                       Print version and exit.
   -h, --help                      Show this message and exit.

 Commands:

   check       Run checks for Loganalyzer
   config      Show or edit the config file
   deeplog     DeepLog method of log anomaly detection
   info        Display information about Loganalyzer.
   loglab      Multi-classification of log anomalies
   loglizer    Loglizer method of log anomaly detection
   oldschool   Analyze logs using oldschool
   preprocess  Preprocess raw logs
   template    Generate and update templates
   utils       Some utils for helping debug/clean logs
