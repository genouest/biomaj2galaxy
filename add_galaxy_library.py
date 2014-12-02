#!/usr/bin/env python
##
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
##

##
# Author: Anthony Bretaudeau <anthony.bretaudeau@rennes.inra.fr>
##

from bioblend_contrib import galaxy
import argparse
import os, sys

def check_input(source, no_file_check):
    if not no_file_check:
        formatted_source = []
        print("Checking input files, converting to absolute path")
        for f in source:
            if not os.path.isfile(f):
                print >> sys.stderr, "ERROR: File '"+f+"' could not be read!"
                sys.exit(1)
            else:
                formatted_source.append(os.path.abspath(f))
        return formatted_source
    else:
        return source

def get_roles(gi, roles):
    """
    Find role ids corresponding to the ones given with -r option
    """
    remotes = gi.roles.get_roles()
    all_remotes = {}
    for r in remotes:
        all_remotes[r['name']] = r['id']
    
    ids = []
    for a in roles:
        if a not in all_remotes:
            print >> sys.stderr, "ERROR: Could not find role '"+a+"'"
            sys.exit(1)
        else:
            ids.append(all_remotes[a])
    
    return ids

def get_library(gi, lib_name, lib_desc, lib_synopsis):
    """
    Get the id corresponding to given library, and create it if it doesn't exist yet
    """
    print("Looking for lib '"+lib_name+"'")
    libs = gi.libraries.get_libraries()

    found_lib = None
    for lib in libs:
        if not found_lib and lib['name'] == lib_name:
            print("Found library '"+lib_name+"'")
            found_lib = lib['id']
            if lib['deleted'] == True:
                print >> sys.stderr, "ERROR: Library '"+lib_name+"' is marked as deleted!"
                print >> sys.stderr, "You have to undelete this library before using tihs script."
                sys.exit(1)

    if not found_lib:
        print("Did not find library '"+lib_name+"', creating it")
        create = gi.libraries.create_library(lib_name, lib_desc, lib_synopsis)
        found_lib = create['id']

    return found_lib

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
        path += "/"+f
        if path in dist_f:
            print("Found folder "+f)
            last_f_id = dist_f[path]['id']
        else:
            print("Did not find folder "+f)
            folder_to_create.append(f)

    if len(folder_to_create) > 0:
        for f in folder_to_create:
            if last_f_id:
                print("Creating folder "+f+" in folder "+last_f_id)
                f_c = gi.libraries.create_folder(found_lib, f, "", last_f_id)
            else:
                print("Creating folder "+f+" in root folder")
                f_c = gi.libraries.create_folder(found_lib, f, "")
            last_f_id = f_c[0]['id']

    return last_f_id

def add_files(gi, lib, dest_folder, source, roles, file_type):
    for f in source:
        gi.libraries.upload_from_galaxy_filesystem(lib, f, dest_folder, file_type, link_data_only = 'link_to_files')
        if roles:
            gi.libraries.set_library_permissions(lib, access_in=roles)

def check_existing(gi, lib, dest, source, replace):

    dest = "/"+"/".join(dest)
    files = []
    for f in source:
        files.append(dest+"/"+os.path.basename(f))
        
    libs = gi.libraries.show_library(lib, True)
    for e in libs:
        if e['type'] == 'file' and e['name'] in files:
            if replace:
                print e['name']+" already present in the data library: replacing it"
                gi.libraries.delete_library_dataset(lib, e['id'])
            else:
                print e['name']+" already present in the data library: adding another copy"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="Url of the galaxy instance", default='http://localhost:8080', required=True)
    parser.add_argument("-k", "--api-key", help="Galaxy API key", required=True)
    parser.add_argument("-l", "--library", help="Data library where the data will be placed", required=True)
    parser.add_argument("-f", "--folder", help="Data library folder where the data will be placed (default=/)")
    parser.add_argument("-r", "--roles", help="Restrict acces to given group(s) (comma separated list). WARNING: the permission of the whole library is modified when using this option.")
    parser.add_argument("--lib-desc", help="Library description (only used if the library does not already exist)")
    parser.add_argument("--lib-synopsis", help="Library synopsis (only used if the library does not already exist)")
    parser.add_argument("--datatype", help="Datatype of the file(s) to add to the data library (default=auto detect)")
    parser.add_argument("--no-file-check", help="This option prevent the script from checking the source files existence.\nThis can be useful for files that are available on the web server running Galaxy, but not on the machine running this script.", action="store_true")
    parser.add_argument("--replace", help="If activated, files already present in the data library (with the same name) will be replaced", action="store_true")
    parser.add_argument("source", nargs="+", help="Path of the file(s) to add to the data library")
    args = parser.parse_args()

    datatype = args.datatype
    if not datatype:
        datatype = "auto"

    source = check_input(args.source, args.no_file_check)

    print("Using galaxy instance '"+args.url+"' with api key '"+args.api_key+"'")

    gi = galaxy.GalaxyContribInstance(url=args.url, key=args.api_key)

    r_roles = []
    if args.roles:
        roles = args.roles.split(',')
        print("Checking roles")
        r_roles = get_roles(gi, roles)

    print("Adding to data library '"+str(args.library)+"'")

    dest = os.path.normpath(args.folder)
    dest = dest.split(os.sep)
    dest = [x for x in dest if x] # Remove empty string when sep at the begin or end, or multiple sep

    found_lib = get_library(gi, args.library, args.lib_desc, args.lib_synopsis)

    print("Preparing folders in library '"+args.library+"'")
    dest_folder = create_tree(gi, found_lib, dest)

    check_existing(gi, found_lib, dest, source, args.replace)

    print("Adding "+str(len(source))+" file(s) to the library '"+args.library+"'")
    add_files(gi, found_lib, dest_folder, source, r_roles, datatype)

    print "Done!"
