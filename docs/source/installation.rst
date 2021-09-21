Install & Run
=============

Dependency
----------

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
- pytorch >= 1.5.0

Installation
------------

At the top directory of loganalyzer clone, run command below to install the analyzer package. Then you can use the "analyzer" command. Type "analyzer --help" for sub commands and options.

pip install .

To get api documents of html format, run command below in docs directory:

make html

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
