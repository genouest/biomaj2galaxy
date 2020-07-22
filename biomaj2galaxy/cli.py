from biomaj2galaxy import __version__
from biomaj2galaxy import pass_context

import click

from .commands.add import add as func0
from .commands.add_lib import add_lib as func2
from .commands.init import init as func4
from .commands.rm import rm as func1
from .commands.rm_lib import rm_lib as func3
from .config import get_instance, global_config_path, set_global_config_path


@click.group()
@click.version_option(__version__)
@click.option('-v', '--verbose', is_flag=True,
              help='Enables verbose mode.')
@click.option(
    "-i",
    "--instance",
    help='Name of instance in %s. This parameter can also be set via the environment variable BM2G_INSTANCE' % global_config_path(),
    default='__default',
    show_default=True,
    required=True
)
@click.option(
    "--path", "-f",
    help="config file path",
    type=str
)
@pass_context
def biomaj2galaxy(ctx, instance, verbose, path=None):
    # set config_path if provided
    if path is not None and len(path) > 0:
        set_global_config_path(path)
    # We abuse this, knowing that calls to one will fail.
    current_ctx = click.get_current_context()
    ctx.gi = None
    try:
        ctx.gi = get_instance(instance)
    except TypeError:
        pass

    if current_ctx.invoked_subcommand not in ['init'] and ctx.gi is None:
        raise Exception("Could not read config file '%s', run `biomaj2galaxy init` to create it, or set BM2G_GLOBAL_CONFIG_PATH to the correct location." % global_config_path())

    ctx.verbose = verbose


biomaj2galaxy.add_command(func0)
biomaj2galaxy.add_command(func1)
biomaj2galaxy.add_command(func2)
biomaj2galaxy.add_command(func3)
biomaj2galaxy.add_command(func4)
