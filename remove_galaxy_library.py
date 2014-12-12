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

def get_library(gi, lib_name):
    """
    Get the id corresponding to given library
    """
    print("Looking for lib '"+lib_name+"'")
    libs = gi.libraries.get_libraries()

    found_lib = None
    for lib in libs:
        if not found_lib and lib['name'] == lib_name and lib['deleted'] == False:
            print("Found library '"+lib_name+"'")
            found_lib = lib['id']

    if not found_lib:
        print >> sys.stderr, "ERROR: Did not find library '"+lib_name+"'"
        sys.exit(1)

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
        path += "/"+f
        if path in dist_f:
            print("Found folder "+f)
            last_f_id = dist_f[path]['id']
        else:
            print >> sys.stderr, "Did not find folder '"+f+"'"
            sys.exit(1)

    return last_f_id

def rm_folder(gi, folder):
    gi.folders.delete_folder(folder, True)

def rm_lib(gi, lib):
    gi.libraries.delete_library(lib)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="Url of the galaxy instance", default='http://localhost:8080', required=True)
    parser.add_argument("-k", "--api-key", help="Galaxy API key", required=True)
    parser.add_argument("-l", "--library", help="Data library where the data should be removed", required=True)
    parser.add_argument("-f", "--folder", help="Data library folder that should be removed (default=/)")
    args = parser.parse_args()

    print("Using galaxy instance '"+args.url+"' with api key '"+args.api_key+"'")

    gi = galaxy.GalaxyContribInstance(url=args.url, key=args.api_key)

    print("Removing from data library '"+str(args.library)+"'")

    found_lib = get_library(gi, args.library)

    if args.folder:
        dest = os.path.normpath(args.folder)
        dest = dest.split(os.sep)
        dest = [x for x in dest if x] # Remove empty string when sep at the begin or end, or multiple sep

        print("Looking for folder '"+args.folder+"' in library '"+args.library+"'")
        dest_folder = find_tree(gi, found_lib, dest)

        print("Removing folder '"+args.folder+"' from the library '"+args.library+"'")
        rm_folder(gi, dest_folder)
    
    else:
        print("Removing library '"+args.library+"'")
        rm_lib(gi, found_lib)

    print "Done!"
