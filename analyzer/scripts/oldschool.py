# Licensed under the MIT License - see License.txt
""" CLI interface to the oldschool module.
"""
import logging
import click
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser
from analyzer.oldschool import OSS


log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# analyzer oldschool run
# ----------------------------------------------------------------------
@click.command(name="run")
@click.option(
    "--learn-ts/--no-learn-ts",
    default=True,
    help="Learn the width of timestamp.",
    show_default=True,
)
def cli_run_oss(learn_ts):
    """ Run the oldshool system module to analyze logs """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'OLDSCHOOL'
    GC.conf['general']['intmdt'] = True

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # Load existing test.txt
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

    # Analyze the structured norm data
    ossobj = OSS(psobj.df_raws)

    # Hand over the line mapping between raw and norm
    ossobj.raw_ln_idx_norm = ppobj.raw_ln_idx_norm

    ossobj.analyze()

    log.info("The logs are analyzed by oldschool module.")
