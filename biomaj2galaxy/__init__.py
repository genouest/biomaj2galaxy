from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

import click

from future import standard_library

from .config import read_global_config

standard_library.install_aliases()

__version__ = '2.2.0'


CONTEXT_SETTINGS = dict(auto_envvar_prefix='BM2G', help_option_names=['-h', '--help'])


class Context(object):

    def __init__(self):
        self.verbose = False
        self.home = os.getcwd()
        self._global_config = None

    @property
    def global_config(self):
        if self._global_config is None:
            self._global_config = read_global_config()
        return self._global_config

    def log(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)

    def exit(self, exit_code):
        self.vlog("Exiting biomaj2galaxy with exit code [%d]" % exit_code)
        sys.exit(exit_code)


pass_context = click.make_pass_decorator(Context, ensure=True)
