# Licensed under the MIT License - see LICENSE.txt
""" Utils to handle yaml file read/write """
import os.path
from pathlib import Path
import shutil
import yaml


__all__ = [
    "read_yaml",
    "read_yaml_pretty",
    "write_yaml",
    "make_path",
    "copy_file",
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

    text = path.read_text(encoding='utf-8')
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

    text = path.read_text(encoding='utf-8')
    dict_format = yaml.safe_load(text)
    pretty_doc = yaml.safe_dump(dict_format, indent=4, sort_keys=False,
                                default_flow_style=False)
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
    text = yaml.safe_dump(dictionary, indent=4, sort_keys=sort_keys,
                          default_flow_style=False)

    path = make_path(filename)
    path.parent.mkdir(exist_ok=True)
    if logger is not None:
        logger.info(f"Writing {path}")
    path.write_text(text, encoding='utf-8')


def make_path(path):
    """ Expand environment variables on `~pathlib.Path` construction.

    Parameters
    ----------
    path : str, `pathlib.Path`
        path to expand
    """
    return Path(os.path.expandvars(path))


def copy_file(dest_file, source_file, logger=None):
    """ Copy file source_file to dest_file.

    Parameters
    ----------
    dest_file : `~pathlib.Path`
        Filename
    source_file : `~pathlib.Path`
        Filename
    logger : `~logging.Logger`
        Logger
    """
    dest_path = make_path(dest_file)
    source_path = Path(source_file)

    if logger is not None:
        logger.info(f"Defaulting {dest_path}")

    shutil.copy(source_path, dest_path)
