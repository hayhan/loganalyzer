# Licensed under the MIT License - see License.txt
""" Utils to handle config file """
import os.path
from pathlib import Path
import yaml

__all__ = [
    "read_yaml",
    "read_yaml_pretty",
    "write_yaml",
    "make_path",
]


def read_yaml(filename, logger=None):
    """ Read YAML file.

    Parameters
    ----------
    filename : `~pathlib.Path`
        Filename
    logger : `~logging.Logger`
        Logger

    Returns
    -------
    data : dict
        YAML file content as a dict
    """
    path = make_path(filename)
    if logger is not None:
        logger.info(f"Reading {path}")

    text = path.read_text()
    return yaml.safe_load(text)


def read_yaml_pretty(filename, logger=None):
    """ Read YAML file with pretty format.

    Parameters
    ----------
    filename : `~pathlib.Path`
        Filename
    logger : `~logging.Logger`
        Logger

    Returns
    -------
    pretty_doc : YAML doc
    """
    path = make_path(filename)
    if logger is not None:
        logger.info(f"Reading {path}")

    text = path.read_text()
    dict_format = yaml.safe_load(text)
    pretty_doc = yaml.safe_dump(dict_format, indent=4, default_flow_style=False,
                            sort_keys=False)
    return pretty_doc


def write_yaml(dictionary, filename, logger=None, sort_keys=False):
    """ Write YAML file.

    Parameters
    ----------
    dictionary : dict
        Python dictionary
    filename : `~pathlib.Path`
        Filename
    logger : `~logging.Logger`
        Logger
    sort_keys : bool
        Whether to sort keys.
    """
    text = yaml.safe_dump(dictionary, indent=4, default_flow_style=False,
                          sort_keys=sort_keys)

    path = make_path(filename)
    path.parent.mkdir(exist_ok=True)
    if logger is not None:
        logger.info(f"Writing {path}")
    path.write_text(text)


def make_path(path):
    """ Expand environment variables on `~pathlib.Path` construction.

    Parameters
    ----------
    path : str, `pathlib.Path`
        path to expand
    """
    # _ToDo: raise error or warning if environment variables that don't resolve are used
    # e.g. "spam/$DAMN/ham" where `$DAMN` is not defined
    return Path(os.path.expandvars(path))
