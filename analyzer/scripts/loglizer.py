# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to the loglizer module.
"""
import os
import sys
import logging
import click
import analyzer.utils.data_helper as dh
import analyzer.utils.yaml_helper as yh
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser
from analyzer.modern.loglizer import Loglizer


log = logging.getLogger(__name__)


# Load profile for exercising Loglizer
EXEC_PROFILE: dict = yh.read_yaml(dh.EXEC_LOGLIZER)

# Classical models (static) for Loglizer
CML_STC_MODELS: dict = EXEC_PROFILE['stc']

# Classical models (incremental/partial) for Loglizer
CML_INC_MODELS: dict = EXEC_PROFILE['inc']

def exercise_all_models(lzobj, sel='all'):
    """ Train/Predict all the models defined by Loglizer """
    if sel == 'stc':
        myiter = CML_STC_MODELS.items()
    elif sel == 'inc':
        myiter = CML_INC_MODELS.items()
    else:  # Exercise all models
        myiter = dict(CML_STC_MODELS, **CML_INC_MODELS).items()

    for model, attr in myiter:
        GC.conf['loglizer']['model'] = model
        GC.conf['loglizer']['window_size'] = attr['window_size']
        GC.conf['loglizer']['window_step'] = attr['window_step']

        if GC.conf['general']['training']:
            lzobj.train()
        elif GC.conf['general']['metrics']:
            lzobj.evaluate()
        else:
            lzobj.predict()


def train_general(is_all, filelst, debug, sel = 'stc'):
    """ General part shared between static and incremental train """
    ppobj = pp.Preprocess()

    ppobj.cat_files_lst(os.path.join(dh.RAW_DATA, 'labeled'), filelst)

    # Process the raw data and generate norm data
    ppobj.preprocess()

    # Extract label info and remove them from norm data
    ppobj.extract_labels()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Train the model for loglizer
    lzobj = Loglizer(psobj.df_raws, psobj.df_tmplts, dbg=debug)
    # Hand over the label info
    lzobj.labels = ppobj.labels

    if is_all:
        exercise_all_models(lzobj, sel)
    else:
        lzobj.train()


# ----------------------------------------------------------------------
# analyzer loglizer train
# ----------------------------------------------------------------------
@click.command(name="train")
@click.option(
    "--model",
    default="NOPE",
    help="Select model to train.",
    show_default=True,
)
@click.option(
    "--inc",
    default=False,
    is_flag=True,
    help="Train model incrementally.",
    show_default=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Debug messages.",
    show_default=True,
)
def cli_loglizer_train(model, inc, debug):
    """ Train the model for loglizer """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overloaded config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = True
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'LOGLIZER'

    # By default, use the model defined in config file
    if model not in ["NOPE", "ALL"]:
        GC.conf['loglizer']['model'] = model

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    # Fetch logs under data/raw/LOG_TYPE/labeled per the list,
    # which provides a time sequence according to timestamps.
    file_loc = os.path.join(dh.RAW_DATA, 'labeled', 'train.lst')
    if not os.path.exists(file_loc):
        print("The train.lst doesn't exist!!!")
        sys.exit(1)
    with open(file_loc, 'r', encoding='utf-8') as fin:
        filelst = [x.strip() for x in fin]

    if inc:
        if GC.conf['loglizer']['model'] not in \
            ['MNB', 'PTN', 'SGDC_SVM', 'SGDC_LR']:
            print("The model cannot be used for incremental learning.")
            sys.exit(1)
        for file in filelst:
            train_general(model=='ALL', [file], debug, sel = 'inc')
    else:
        train_general(model=='ALL', filelst, debug, sel = 'stc')

    log.info("The loglizer model training done.")


# ----------------------------------------------------------------------
# analyzer loglizer validate
# ----------------------------------------------------------------------
@click.command(name="validate")
@click.option(
    "--model",
    default="NOPE",
    help="Select model to validate.",
    show_default=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Debug messages.",
    show_default=True,
)
@click.option(
    "--src",
    default="NOPE",
    help="Validate all the files in the given folder.",
    show_default=True,
)
def cli_loglizer_validate(model, debug, src):
    """ Validate the model for loglizer """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overloaded config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = True
    GC.conf['general']['context'] = 'LOGLIZER'

    # By default, use the model defined in config file
    if model not in ["NOPE", "ALL"]:
        GC.conf['loglizer']['model'] = model

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # If option src has given folder in data/raw/LOG_TYPE/, concatenate
    # the logs under the given folder, and validate that one. Otherwise
    # validate the existing test.txt in data/cooked/LOG_TYPE/.
    if src != "NOPE":
        # Concatenate logs under data/raw/LOG_TYPE/src per the list,
        # which provides a time sequence according to timestamps.
        file_loc = os.path.join(dh.RAW_DATA, src, 'validate.lst')
        if not os.path.exists(file_loc):
            print("The validate.lst doesn't exist!!!")
            sys.exit(1)
        with open(file_loc, 'r', encoding='utf-8') as fin:
            filelst = [x.strip() for x in fin]

        ppobj.cat_files_lst(os.path.join(dh.RAW_DATA, 'labeled'), filelst)
    else:
        # Load existing test.txt for validation
        ppobj.load_raw_logs()

    # Process the raw data and generate norm data
    ppobj.preprocess()

    # Remove the abnormal labels from norm data if any exist
    ppobj.extract_labels()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Validate the model for loglizer
    lzobj = Loglizer(psobj.df_raws, psobj.df_tmplts, dbg=debug)

    # Hand over label info for validation
    lzobj.labels = ppobj.labels

    if model == 'ALL':
        exercise_all_models(lzobj)
    else:
        lzobj.evaluate()

    log.info("The loglizer model validation done.")


# ----------------------------------------------------------------------
# analyzer loglizer predict
# ----------------------------------------------------------------------
@click.command(name="predict")
@click.option(
    "--model",
    default="NOPE",
    help="Select model to predict.",
    show_default=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Debug messages.",
    show_default=True,
)
def cli_loglizer_predict(model, debug):
    """ Predict logs by using loglizer model """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overloaded config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'LOGLIZER'

    # By default, use the model defined in config file
    if model not in ["NOPE", "ALL"]:
        GC.conf['loglizer']['model'] = model

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # Load existing test.txt for prediction
    ppobj.load_raw_logs()

    # Process the raw data and generate norm data
    ppobj.preprocess()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Predict using loglizer model
    lzobj = Loglizer(psobj.df_raws, psobj.df_tmplts, dbg=debug)

    if model == 'ALL':
        exercise_all_models(lzobj)
    else:
        lzobj.predict()

    log.info("The logs are predicted using loglizer.")


# ----------------------------------------------------------------------
# analyzer loglizer show
# ----------------------------------------------------------------------
@click.command(name="show")
def cli_loglizer_show():
    """ Show supported models """
    desc: str = (
        "\n----------Supported models (Static)----------\n"
        "- DT       : Decision Tree\n"
        "- RFC      : Random Forrest Classification\n"
        "- LR       : Logistic Regression\n"
        "- SVM      : Supported Vector Machine\n"
        "- ALL      : Train all models in one shot"
        "\n----------Supported models (Partial)--------\n"
        "- MNB      : Multinomial Naive Bayes\n"
        "- PTN      : Linear perceptron classifier\n"
        "- SGDC_SVM : Stochastic gradient descent SVM\n"
        "- SGDC_LR  : Stochastic gradient descent LR\n"
        "- ALL      : Train all models in one shot"
        "\n--------------------------------------------\n"
    )
    print(desc)

    log.info("The logs are predicted using loglab.")
