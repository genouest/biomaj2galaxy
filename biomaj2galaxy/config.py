from __future__ import absolute_import

import os

from bioblend import galaxy

import yaml


DEFAULT_CONFIG = {
}

_config_path = os.environ.get(
    "BM2G_GLOBAL_CONFIG_PATH",
    "~/.bm2g.yml"
)
_config_path = os.path.expanduser(_config_path)
DEFAULT_CONFIG['config_path'] = _config_path


def global_config_path():
    return DEFAULT_CONFIG['config_path']


def set_global_config_path(config_path):
    DEFAULT_CONFIG['config_path'] = config_path


def read_global_config():
    config_path = global_config_path()
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG

    with open(config_path) as f:
        return yaml.load(f)


def _get_instance(instance_name=None):
    # I don't like reading the config twice.
    conf = read_global_config()

    if not os.path.exists(global_config_path()):
        # Probably creating the file for the first time.
        return None

    if instance_name is None or instance_name == '__default':
        try:
            instance_name = conf['__default']
        except KeyError:
            raise Exception("Unknown Galaxy instance and no __default provided")

    if instance_name not in conf:
        raise Exception("Unknown Galaxy instance; check spelling or add to %s" % DEFAULT_CONFIG)

    return conf[instance_name]


def get_instance(instance_name=None, offline=False):
    conf = _get_instance(instance_name=instance_name)
    return galaxy.GalaxyInstance(url=conf['url'],
                                 key=conf['apikey'],)
