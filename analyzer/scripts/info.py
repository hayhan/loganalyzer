# Licensed under the MIT License - see License.txt
""" Version and system information.
"""
import importlib
import logging
import os
import platform
import sys
import warnings
import click
from analyzer import __version__

log = logging.getLogger(__name__)

# See setup.cfg
LOGANALYZER_DEPENDENCIES = [
    # required
    "numpy",
    "scipy",
    "sklearn",
    "pandas",
    "matplotlib",
    "skl2onnx",
    "onnxruntime",
    "click",
    "tqdm",
    # optional
    "pylint",
    "pep8",
    "autopep8",
    "flake8",
]

LOGANALYZER_ENV_VARIABLES = ["LOGANALYZER_DATA"]


@click.command(name="info")
@click.option("--system/--no-system", default=True, help="Show system info")
@click.option("--version/--no-version", default=True, help="Show version")
@click.option("--dependencies/--no-dependencies", default=True, help="Show dependencies")
@click.option("--envvar/--no-envvar", default=True, help="Show environment variables")
def cli_info(system, version, dependencies, envvar):
    """ Display information about Loganalyzer. """
    if system:
        info = get_info_system()
        print_info(info=info, title="System")

    if version:
        info = get_info_version()
        print_info(info=info, title="Loganalyzer package")

    if dependencies:
        info = get_info_dependencies()
        print_info(info=info, title="Other packages")

    if envvar:
        info = get_info_envvar()
        print_info(info=info, title="Loganalyzer environment variables")


def print_info(info, title):
    """ Print Loganalyzer info. """
    info_all = f"\n{title}:\n\n"

    for key, value in info.items():
        info_all += f"\t{key:22s} : {value:<10s} \n"

    print(info_all)


def get_info_system():
    """ Get info about user system. """
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
    }


def get_info_version():
    """ Get detailed info about Loganalyzer version. """
    info = {"version": __version__}
    try:
        path = sys.modules["analyzer"].__path__[0]
    except:
        path = "unknown"
    info["path"] = path

    return info


def get_info_dependencies():
    """ Get info about Loganalyzer dependencies. """
    info = {}
    for name in LOGANALYZER_DEPENDENCIES:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                module = importlib.import_module(name)

            module_version = getattr(module, "__version__", "no version info found")
        except ImportError:
            module_version = "not installed"
        info[name] = module_version
    return info


def get_info_envvar():
    """ Get info about Loganalyzer environment variables. """
    return {name: os.environ.get(name, "not set") for name in LOGANALYZER_ENV_VARIABLES}
