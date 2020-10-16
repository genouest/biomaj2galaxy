from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from biomaj2galaxy import pass_context
from biomaj2galaxy.utils import find_tree, get_library

import click


@click.command()
@click.argument("library", nargs=1)
@click.option(
    "-f",
    "--folder",
    help="Data library folder to remove (default=remove the whole library)",
    type=str
)
@pass_context
def rm_lib(ctx, library, folder):
    """Remove data from the LIBRARY Galaxy data library"""

    print("Removing from data library '" + str(library) + "'")

    found_lib = get_library(ctx.gi, library)

    if folder:
        dest = os.path.normpath(folder)
        dest = dest.split(os.sep)
        dest = [x for x in dest if x]  # Remove empty string when sep at the begin or end, or multiple sep

        print("Looking for folder '" + folder + "' in library '" + library + "'")
        dest_folder = find_tree(ctx.gi, found_lib, dest)

        print("Removing folder '" + folder + "' from the library '" + library + "'")
        ctx.gi.folders.delete_folder(dest_folder, True)

    else:
        print("Removing the whole library '" + library + "'")
        ctx.gi.libraries.delete_library(found_lib)

    print("Done!")
