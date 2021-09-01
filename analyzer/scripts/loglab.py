# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to the loglab module.
"""
import logging
import click
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser
from analyzer.modern.loglab import Loglab


log = logging.getLogger(__name__)

# Classical models for Loglab
CML_MODELS = {
    'RFC': {'win_size': 10, 'weight': 2},
    'LR': {'win_size': 10, 'weight': 2},
    'SVM': {'win_size': 10, 'weight': 2},
}


def exercise_all_models(llobj):
    """ Train/Predict all the models defined by Loglab """
    for model, attr in CML_MODELS.items():
        GC.conf['loglab']['model'] = model
        GC.conf['loglab']['window_size'] = attr['win_size']
        GC.conf['loglab']['weight'] = attr['weight']

        if GC.conf['general']['training']:
            llobj.train()
        else:
            llobj.predict()


# ----------------------------------------------------------------------
# analyzer loglab train
# ----------------------------------------------------------------------
@click.command(name="train")
@click.option(
    "--model",
    default="NOPE",
    help="Select model to train.",
    show_default=True,
)
@click.option(
    "--adm",
    default=False,
    is_flag=True,
    help="Train all defined models.",
    show_default=True,
)
@click.option(
    "--mykfold",
    default=False,
    is_flag=True,
    help="Select manual kfold implementation.",
    show_default=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Debug messages.",
    show_default=True,
)
def cli_loglab_train(model, adm, mykfold, debug):
    """ Train the model for loglab """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = True
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'LOGLAB'

    if mykfold:
        GC.conf['loglab']['mykfold'] = True

    # By default, use the model defined in config file
    if model != "NOPE":
        GC.conf['loglab']['model'] = model

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # Concatenate the logs under data/raw/LOG_TYPE/loglab
    ppobj.cat_files_loglab()

    # Process the raw data and generate new data
    ppobj.preprocess_new()

    # Normalize the new data to generate norm data
    ppobj.preprocess_norm()

    # Extract class info and remove them from norm data
    ppobj.segment_loglab()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Train the model for loglab
    llobj = Loglab(psobj.df_raws, psobj.df_tmplts, dbg=debug)

    # Hand over segment info for training
    llobj.segll = ppobj.segll

    if adm:
        exercise_all_models(llobj)
    else:
        llobj.train()

    log.info("The loglab model training done.")


# ----------------------------------------------------------------------
# analyzer loglab predict
# ----------------------------------------------------------------------
@click.command(name="predict")
@click.option(
    "--model",
    default="NOPE",
    help="Select model to train.",
    show_default=True,
)
@click.option(
    "--adm",
    default=False,
    is_flag=True,
    help="Predict using all defined models.",
    show_default=True,
)
@click.option(
    "--learn-ts/--no-learn-ts",
    default=True,
    help="Learn the width of timestamp.",
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
    "--feat",
    default=False,
    is_flag=True,
    help="Display the features of test logs.",
    show_default=True,
)
def cli_loglab_predict(model, adm, learn_ts, debug, feat):
    """ Predict logs by using loglab model """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'LOGLAB'

    # By default, use the model defined in config file
    if model != "NOPE":
        GC.conf['loglab']['model'] = model

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # Load existing test.txt for prediction
    ppobj.load_raw_logs()

    # By default, learn the width of timestamp
    if learn_ts:
        ppobj.preprocess_ts()
        ps_ts_obj = Parser(ppobj.normlogs)
        ps_ts_obj.parse()
        ps_ts_obj.det_timestamp()

    # Process the raw data and generate new data
    ppobj.preprocess_new()

    # Normalize the new data to generate norm data
    ppobj.preprocess_norm()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Predict using loglab model
    if feat:
        debug = True

    llobj = Loglab(psobj.df_raws, psobj.df_tmplts, dbg=debug)

    if feat:
        llobj.check_feature()
    elif adm:
        exercise_all_models(llobj)
    else:
        llobj.predict()

    log.info("The logs are predicted using loglab.")
