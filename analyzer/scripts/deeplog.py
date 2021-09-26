# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to the deeplog module.
"""
import os
import logging
import click
import analyzer.utils.data_helper as dh
import analyzer.utils.yaml_helper as yh
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser
from analyzer.modern.deeplog import DeepLog


log = logging.getLogger(__name__)


# Load profile for exercising DeepLog Exec/LSTM model
PARA_GROUPS: dict = yh.read_yaml(dh.EXEC_DEEPLOG)

def exercise_all_para_groups(dlobj):
    """ Train/Predict all the model parameter groups """
    for group, attr in PARA_GROUPS.items():
        GC.conf['deeplog']['para_group'] = group
        GC.conf['deeplog']['window_size'] = attr['window_size']
        GC.conf['deeplog']['batch_size'] = attr['batch_size']
        GC.conf['deeplog']['num_epochs'] = attr['num_epochs']
        GC.conf['deeplog']['hidden_size'] = attr['hidden_size']
        GC.conf['deeplog']['topk'] = attr['topk']
        GC.conf['deeplog']['num_dir'] = attr['num_dir']
        GC.conf['deeplog']['num_workers'] = attr['num_workers']
        GC.conf['deeplog']['device'] = attr['device']

        if GC.conf['general']['training']:
            dlobj.train()
        elif GC.conf['general']['metrics']:
            dlobj.evaluate()
        else:
            dlobj.predict()


# ----------------------------------------------------------------------
# analyzer deeplog train
# ----------------------------------------------------------------------
@click.command(name="train")
@click.option(
    "--adm",
    default=False,
    is_flag=True,
    help="Train all defined model parameter groups.",
    show_default=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Debug messages.",
    show_default=True,
)
def cli_deeplog_train(adm, debug):
    """ Train the model for deeplog """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overloaded config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = True
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'DEEPLOG'

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # Concatenate the logs under data/raw/LOG_TYPE/normal
    ppobj.cat_files_deeplog(os.path.join(dh.RAW_DATA, 'normal'))

    # Process the raw data and generate norm data
    ppobj.preprocess()

    # Extract segment info and remove them from norm data
    ppobj.segment_deeplog()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Train the model for deeplog
    dlobj = DeepLog(psobj.df_raws, psobj.df_tmplts, dbg=debug)

    # Hand over segment info for training
    dlobj.segdl = ppobj.segdl

    if adm:
        exercise_all_para_groups(dlobj)
    else:
        dlobj.train()

    log.info("The deeplog model training done.")


# ----------------------------------------------------------------------
# analyzer deeplog validate
# ----------------------------------------------------------------------
@click.command(name="validate")
@click.option(
    "--adm",
    default=False,
    is_flag=True,
    help="Validate all defined model parameter groups.",
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
def cli_deeplog_validate(adm, debug, src):
    """ Validate the model for deeplog """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overloaded config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = True
    GC.conf['general']['context'] = 'DEEPLOG'

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # If option src has given folder in data/raw/LOG_TYPE/, concatenate
    # the logs under the given folder, and validate that one. Otherwise
    # validate the existing test.txt in data/cooked/LOG_TYPE/.
    if src != "NOPE":
        ppobj.cat_files_deeplog(os.path.join(dh.RAW_DATA, src))
    else:
        # Load existing test.txt for validation
        ppobj.load_raw_logs()

    # Process the raw data and generate norm data
    ppobj.preprocess()

    # Remove the abnormal labels from norm data if any exist. And then
    # extract segment info. Do NOT inverse them.
    ppobj.extract_labels()

    # Extract segment info and remove them from norm data
    ppobj.segment_deeplog()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Validate the model for deeplog
    dlobj = DeepLog(psobj.df_raws, psobj.df_tmplts, dbg=debug)

    # Hand over segment info and label info for validation
    dlobj.segdl = ppobj.segdl
    dlobj.labels = ppobj.labels

    if adm:
        exercise_all_para_groups(dlobj)
    else:
        dlobj.evaluate()

    log.info("The deeplog model validation done.")


# ----------------------------------------------------------------------
# analyzer deeplog predict
# ----------------------------------------------------------------------
@click.command(name="predict")
@click.option(
    "--adm",
    default=False,
    is_flag=True,
    help="Predict all defined model parameter groups.",
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
def cli_deeplog_predict(adm, learn_ts, debug):
    """ Predict logs by using deeplog model """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overloaded config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'DEEPLOG'

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

    # Process the raw data and generate norm data
    ppobj.preprocess()

    # Parse the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    # Recover the messed logs per the setting in config file
    if GC.conf['general']['rcv_mess']:
        psobj.map_norm_raw = ppobj.map_norm_raw
        # Recover logs using structured norm data from the 1st parsing
        psobj.rcv_mess()
        # Parse again the recovered norm data
        ps_rcv_obj = Parser(psobj.norm_rcv, rcv=True)
        ps_rcv_obj.parse()
        # Until now, psobj.df_raws is the 1st time structured norm.
        # ps_rcv_obj.df_raws is the 2nd time structured norm data.

        # Predict using deeplog model
        dlobj = DeepLog(ps_rcv_obj.df_raws, ps_rcv_obj.df_tmplts, dbg=debug)
        # Provide the 1st time structured norm for OSS para detection
        dlobj.df_raws_o = psobj.df_raws
        # Hand over mapping between raw and norm_rcv for prediction
        dlobj.map_norm_raw = psobj.map_norm_raw
        # Hand over mapping between norm and norm_rcv
        dlobj.map_norm_rcv = psobj.map_norm_rcv
    else:
        # Predict using deeplog model
        dlobj = DeepLog(psobj.df_raws, psobj.df_tmplts, dbg=debug)
        # Hand over mapping between raw and norm for prediction
        dlobj.map_norm_raw = ppobj.map_norm_raw

    if adm:
        exercise_all_para_groups(dlobj)
    else:
        dlobj.predict()

    log.info("The logs are predicted using deeplog.")
