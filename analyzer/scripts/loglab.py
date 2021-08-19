# Licensed under the MIT License - see License.txt
""" CLI interface to the loglab module.
"""
import logging
import click
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser
from analyzer.modern.loglab import Loglab


log = logging.getLogger(__name__)

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
def cli_loglab_train(model):
    """ Train the model for loglab """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = True
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'LOGLAB'
    GC.conf['general']['intmdt'] = True

    # By default, use the model defined in config file
    if model != "NOPE":
        GC.conf['loglab']['model'] = model

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # Concatenate the logs under data/raw/LOG_TYPE/loglab
    ppobj.cat_files_loglab()
    ppobj.load_raw_logs()

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
    llobj = Loglab(psobj.df_raws, psobj.df_tmplts, ppobj.segll)
    llobj.train()

    log.info("The model is trained for loglab.")


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
    "--learn-ts/--no-learn-ts",
    default=True,
    help="Learn the width of timestamp.",
    show_default=True,
)
def cli_loglab_predict(model, learn_ts):
    """ Predict logs by using loglab model """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'LOGLAB'
    GC.conf['general']['intmdt'] = True

    # By default, use the model defined in config file
    if model != "NOPE":
        GC.conf['loglab']['model'] = model

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()
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
    llobj = Loglab(psobj.df_raws, psobj.df_tmplts, ppobj.segll)
    llobj.predict()

    log.info("The logs are predicted using loglab.")
