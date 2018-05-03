from biomaj2galaxy.config import get_instance

gi = get_instance('local')


def setup_package():
    global gi
