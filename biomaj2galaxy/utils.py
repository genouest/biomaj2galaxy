from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import fnmatch
import os
import sys
import time

from bioblend import ConnectionError

from biomaj2galaxy.io import warn


def get_roles(gi, roles):
    """
    Find role ids corresponding to the ones given with -r option
    """
    remotes = gi.roles.get_roles()
    remotes = {r['name']: r['id'] for r in remotes}

    ids = []
    for a in roles:
        if a not in remotes:
            raise Exception("Could not find role '" + a + "'")
        else:
            ids.append(remotes[a])

    return ids


def isfile_wo_ext(path):
    """Checks that a file exists, or exists with any extension"""
    path_dir = os.path.dirname(path)
    path_fn = os.path.basename(path)

    return os.path.isfile(path) or len(fnmatch.filter(os.listdir(path_dir), path_fn + '.*')) > 0


def check_input(sources, check_existence=True, use_biomaj_env=True):
    formatted_source = []
    print("Checking input files, converting to absolute path: %s" % sources)
    for f in sources:
        if use_biomaj_env and not f.startswith('/') and 'data.dir' in os.environ and 'dirversion' in os.environ and 'localrelease' in os.environ:
            abs_path = os.path.join(os.environ['data.dir'], os.environ['dirversion'], os.environ['localrelease'], f)
        else:
            abs_path = os.path.abspath(f)

        if check_existence and not isfile_wo_ext(abs_path):
            raise Exception("File '" + abs_path + "' could not be read!")

        formatted_source.append(abs_path)
    return formatted_source


def get_library(gi, lib_name, lib_desc="", lib_synopsis="", create=True):
    """
    Get the id corresponding to given library, and create it if it doesn't exist yet
    """
    print("Looking for lib '" + lib_name + "'")
    libs = gi.libraries.get_libraries()

    found_lib = None
    for lib in libs:
        if not found_lib and lib['name'] == lib_name and lib['deleted'] is False:
            print("Found library '" + lib_name + "'")
            found_lib = lib['id']

    if not found_lib:
        if create:
            print("Did not find library '" + lib_name + "', creating it")
            create = gi.libraries.create_library(lib_name, lib_desc, lib_synopsis)
            found_lib = create['id']
        else:
            raise Exception("Did not find library '" + lib_name + "'")

    return found_lib


def find_tree(gi, found_lib, folders):
    """
    Look for a directory structure in the given library.
    Returns the id of the last folder of the tree if it was completely found
    """
    dist_folders = gi.libraries.get_folders(found_lib)

    dist_f = {}
    for f in dist_folders:
        dist_f[f['name']] = f

    path = ""
    last_f_id = None
    for f in folders:
        path += "/" + f
        if path in dist_f:
            print("Found folder " + f)
            last_f_id = dist_f[path]['id']
        else:
            raise Exception("Did not find folder '" + f + "'")

    return last_f_id


def create_tree(gi, found_lib, folders):
    """
    Create a directory structure in the given library.
    Returns the id of the last folder of the tree
    """
    dist_folders = gi.libraries.get_folders(found_lib)

    dist_f = {}
    for f in dist_folders:
        dist_f[f['name']] = f

    path = ""
    last_f_id = None
    folder_to_create = []
    for f in folders:
        path += "/" + f
        if path in dist_f:
            print("Found folder " + f)
            last_f_id = dist_f[path]['id']
        else:
            print("Did not find folder " + f)
            folder_to_create.append(f)

    if len(folder_to_create) > 0:
        for f in folder_to_create:
            if last_f_id:
                print("Creating folder " + f + " in folder " + last_f_id)
                f_c = gi.libraries.create_folder(found_lib, f, "", last_f_id)
            else:
                print("Creating folder " + f + " in root folder")
                f_c = gi.libraries.create_folder(found_lib, f, "")
            last_f_id = f_c[0]['id']

    return last_f_id


def add_files(gi, lib, dest_folder, source, roles, file_type):
    for f in source:
        gi.libraries.upload_from_galaxy_filesystem(lib, f, dest_folder, file_type, link_data_only='link_to_files')
        if roles:
            gi.libraries.set_library_permissions(lib, access_in=roles)


def check_existing(gi, lib, dest, source, replace):

    dest = "/" + "/".join(dest)
    files = []
    for f in source:
        files.append(dest + "/" + os.path.basename(f))

    libs = gi.libraries.show_library(lib, True)
    for e in libs:
        if e['type'] == 'file' and e['name'] in files:
            if replace:
                print(e['name'] + " already present in the data library: replacing it")
                gi.libraries.delete_library_dataset(lib, e['id'])
            else:
                print(e['name'] + " already present in the data library: adding another copy")


def get_dbkey_entry(gi, dbkey):
    dbkeys = gi.tool_data.show_data_table('__dbkeys__')

    for k in dbkeys['fields']:
        if k[0] == dbkey:
            return k


def wait_completion(gi, dataset_id, job_id, sleep_time=30, exit_on_error=True):
    error_number = 0
    sleep_time = 10  # Don't wait too much for first try

    dataset_info = []
    while True:
        # What's the status of the running job?
        try:
            dataset_info = gi.datasets.show_dataset(dataset_id)
        except ConnectionError:
            error_number += 1
            warn("Could not connect to the Galaxy server, waiting %s seconds before retrying..." % (sleep_time * error_number))
            time.sleep(sleep_time * (error_number - 1))  # -1 because we already wait a little below

            if error_number > 50:
                raise Exception('Could not connect to the Galaxy server for too long, giving up.')

        # Finished!
        if dataset_info and 'state' in dataset_info and dataset_info['state'] in ['ok', 'error']:
            break

        # Not finished yet, wait a little
        time.sleep(sleep_time)
        sleep_time = 30

    dataset_info = gi.datasets.show_dataset(dataset_id)
    status = dataset_info['state']
    if exit_on_error and status == 'error' and job_id is not None:
        details = gi.jobs.show_job(job_id, full_details=True)
        print("STDOUT content:")
        print(details['stdout'])
        print("STDERR content:", file=sys.stderr)
        print(details['stderr'], file=sys.stderr)
        raise Exception("Job finished in error state! Aborting")
