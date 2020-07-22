from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from biomaj2galaxy import pass_context
from biomaj2galaxy.utils import add_files, check_existing, check_input, create_tree, get_library, get_roles

import click


@click.command()
@click.argument("sources", nargs=-1, type=click.Path())
@click.option(
    "-l",
    "--library",
    help="Name of the destination library (default=guessed from BioMAJ bank name, ie $dbname env var)",
    type=str
)
@click.option(
    "-f",
    "--folder",
    help="Data library folder where the data will be placed (default=/)",
    default="/",
    type=str
)
@click.option(
    "--roles",
    help="Restrict acces to given role(s) (comma separated list). WARNING: the permission of the whole library is modified when using this option.",
    default="",
    type=str
)
@click.option(
    "--lib-desc",
    help="Library description (only used if the library does not already exist)",
    default="",
    type=str
)
@click.option(
    "--lib-synopsis",
    help="Library synopsis (only used if the library does not already exist)",
    default="",
    type=str
)
@click.option(
    "--datatype",
    help="Datatype of the file(s) to add to the data library (default=auto detect)",
    default="auto",
    type=str
)
@click.option(
    "--no-file-check",
    help="Don't check the source files existence.\nUseful for files that are available on the Galaxy server, but not on the machine running this script.",
    is_flag=True
)
@click.option(
    "--replace",
    help="Replace files already present in the data library (with the same name)",
    is_flag=True
)
@click.option(
    "--no-biomaj-env",
    help="Add this flag if you don't want biomaj2galaxy to use BioMAJ env variables to guess file names.",
    is_flag=True
)
@pass_context
def add_lib(ctx, sources, library, folder, roles, lib_desc, lib_synopsis, datatype, no_file_check, replace, no_biomaj_env):
    """Add data to a Galaxy data library, where SOURCES a list of file/directories to add."""

    if not sources:
        print("Nothing to do")
        return

    if not library:
        if 'dbname' in os.environ:
            library = os.environ['dbname']
        else:
            raise Exception('No library defined. Use the --library option.')

    sources = check_input(sources, check_existence=(not no_file_check), use_biomaj_env=(not no_biomaj_env))

    r_roles = []
    if roles:
        print("Checking roles")
        roles = roles.split(',')
        r_roles = get_roles(ctx.gi, roles)

    print("Adding to data library '" + str(library) + "'")

    if not folder:
        folder = '/'
    dest = os.path.normpath(folder)
    dest = dest.split(os.sep)
    dest = [x for x in dest if x]  # Remove empty string when sep at the begin or end, or multiple sep

    found_lib = get_library(ctx.gi, library, lib_desc, lib_synopsis)

    print("Preparing folders in library '" + library + "'")

    dest_folder = create_tree(ctx.gi, found_lib, dest)

    check_existing(ctx.gi, found_lib, dest, sources, replace)

    print("Adding " + str(len(sources)) + " file(s) to the library '" + library + "'")
    add_files(ctx.gi, found_lib, dest_folder, sources, r_roles, datatype)

    print("Done!")
