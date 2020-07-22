# coding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from bioblend import galaxy

from biomaj2galaxy import config, pass_context
from biomaj2galaxy.io import info, warn

import click


CONFIG_TEMPLATE = """## BioMAJ2Galaxy: Global Configuration File.
# Each stanza should contain a single Galaxy server to interact with.
#
# You can set the key __default to the name of a default instance
__default: local

local:
    url: "%(url)s"
    apikey: "%(apikey)s"
"""

SUCCESS_MESSAGE = (
    "Ready to go! Type `biomaj2galaxy` to get a list of commands you can execute."
)


@click.command()
@pass_context
def init(ctx, url=None, api_key=None, admin=False, **kwds):
    """Help initialize global configuration (in home directory)
    """

    click.echo("""Welcome to BioMAJ2Galaxy""")
    if os.path.exists(config.global_config_path()):
        info("Your biomaj2galaxy configuration already exists. Please edit it instead: %s" % config.global_config_path())
        return 0

    while True:
        # Check environment
        url = click.prompt("url")
        apikey = click.prompt("apikey")

        info("Testing connection...")
        try:
            instance = galaxy.GalaxyInstance(url=url, key=apikey)
            instance.libraries.get_libraries()
            # We do a connection test during startup.
            info("Ok! Everything looks good.")
            break
        except Exception as e:
            warn("Error, we could not access the configuration data for your instance: %s", e)
            should_break = click.prompt("Continue despite inability to contact this instance? [y/n]")
            if should_break in ('Y', 'y'):
                break

    config_path = config.global_config_path()
    if os.path.exists(config_path):
        warn("File %s already exists, refusing to overwrite." % config_path)
        return -1

    with open(config_path, "w") as f:
        f.write(CONFIG_TEMPLATE % {
            'url': url,
            'apikey': apikey,
        })
        info(SUCCESS_MESSAGE)
