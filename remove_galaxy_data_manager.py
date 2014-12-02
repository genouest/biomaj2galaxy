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

import os
import sys
import argparse
import urlparse
import time

from bioblend_contrib import galaxy

def get_table_entries(gi, table, entry_id, field = 0):

    entries = gi.tool_data.show_data_table(table)
    
    matches = []
    
    for line in entries['fields']:
        if line[field] == entry_id:
            matches.append(line)

    return matches

def remove_table_entry(gi, table, cols):

    print "Deleting from '"+table+"' table"
    gi.tool_data.delete_data_table(table, "\t".join(cols))

def remove_files(path, links_only = True, extensions = []):
    if extensions:
        for ext in extensions:
            if os.path.isfile(path+ext):
                if (links_only and os.path.islink(path+ext)) or not links_only:
                    print "Removing file "+path+ext
                    os.remove(path+ext)
                elif links_only:
                    print >> sys.stderr, "Could not remove file "+path+ext+" (not a symlink)"
            else:
                print >> sys.stderr, "Could not remove file "+path+ext+" (not found)"
    else:
        if os.path.isfile(path):
            if (links_only and os.path.islink(path)) or not links_only:
                print "Removing file "+path
                os.remove(path)
            elif links_only:
                print >> sys.stderr, "Could not remove file "+path+" (not a symlink)"
        else:
            print >> sys.stderr, "Could not remove file "+path+" (not found)"

if __name__ == '__main__':
    #Parse Command Line
    parser = argparse.ArgumentParser()
    parser.add_argument( '-u', '--url', default='http://localhost:8080', help='Url of the galaxy instance', required=True)
    parser.add_argument( '-k', '--api-key', help='Galaxy API key', required=True)
    parser.add_argument( '-d', '--dbkey', help='Dbkey to remove (i.e. genome build like \'hg19\')', required=True)
    
    # Index pregenerated
    parser.add_argument( '-f', '--fasta', help='Remove given dbkey from the list of fasta files', action="store_true")
    parser.add_argument( '--blastn', help='Remove given id from the list of pregenerated Blast nucleotide databank', action="store_true")
    parser.add_argument( '--blastp', help='Remove given id from the list of pregenerated Blast protein databank', action="store_true")
    parser.add_argument( '--bowtie', help='Remove given dbkey from the list of pregenerated Bowtie index', action="store_true")
    parser.add_argument( '--bowtie2', help='Remove given dbkey from the list of pregenerated Bowtie2 index', action="store_true")
    parser.add_argument( '--bwa', help='Remove given dbkey from the list of pregenerated BWA index', action="store_true")
    parser.add_argument( '--twobit', help='Remove given dbkey from the list of pregenerated 2bit index (UCSC)', action="store_true")
    
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument( '--delete', help='Remove from disk the files referenced in the data tables (except len files from __dbkeys__)', action="store_true")
    group.add_argument( '--delete-links', help='Remove from disk the files referenced in the data tables, only if they are symlinks (except len files from __dbkeys__)', action="store_true")

    parser.add_argument( '--delete-len', help='Remove from disk the len file referenced in the __dbkeys__ data table', action="store_true")
    
    # TODO support other tables: tophat, tophat2, fasta_indexes, twobit
    
    args = parser.parse_args()
    
    gi = galaxy.GalaxyContribInstance(url=args.url, key=args.api_key)

    # Always delete from the __dbkeys__ table
    table = '__dbkeys__'
    table_entries = get_table_entries(gi, table, args.dbkey)
    if table_entries:
        for entry in table_entries:
            remove_table_entry(gi, table, entry)
            if args.delete_len:
                remove_files(entry[2], True)

    if args.fasta:
        table = 'all_fasta'
        table_entries = get_table_entries(gi, table, args.dbkey, 1)
        if table_entries:
            for entry in table_entries:
                remove_table_entry(gi, table, entry)
                if args.delete or args.delete_links:
                    remove_files(entry[3], args.delete_links)

    if args.blastn:        
        table = 'blastdb'
        table_entries = get_table_entries(gi, table, args.dbkey)
        if table_entries:
            for entry in table_entries:
                remove_table_entry(gi, table, entry)
                if args.delete or args.delete_links:
                    remove_files(entry[2], args.delete_links, ['nal', 'nhr', 'nin', 'nnd', 'nni', 'nsd', 'nsi', 'nsq']) # FIXME handle multi volume databanks

    if args.blastp:        
        table = 'blastdb_p'
        table_entries = get_table_entries(gi, table, args.dbkey)
        if table_entries:
            for entry in table_entries:
                remove_table_entry(gi, table, entry)
                if args.delete or args.delete_links:
                    remove_files(entry[2], args.delete_links, ['pal', 'phr', 'pin', 'pnd', 'pni', 'psd', 'psi', 'psq']) # FIXME handle multi volume databanks

    if args.bowtie:        
        table = 'bowtie_indexes'
        table_entries = get_table_entries(gi, table, args.dbkey, 1)
        if table_entries:
            for entry in table_entries:
                remove_table_entry(gi, table, entry)
                if args.delete or args.delete_links:
                    remove_files(entry[3], args.delete_links, ['.1.ebwt', '.2.ebwt', '.3.ebwt', '.4.ebwt', '.rev.1.ebwt', '.rev.2.ebwt'])

    if args.bowtie2:        
        table = 'bowtie2_indexes'
        table_entries = get_table_entries(gi, table, args.dbkey, 1)
        if table_entries:
            for entry in table_entries:
                remove_table_entry(gi, table, entry)
                if args.delete or args.delete_links:
                    remove_files(entry[3], args.delete_links, ['.1.bt2', '.2.bt2', '.3.bt2', '.4.bt2', '.rev.1.bt2', '.rev.2.bt2'])

    if args.bwa:        
        table = 'bwa_indexes'
        table_entries = get_table_entries(gi, table, args.dbkey, 1)
        if table_entries:
            for entry in table_entries:
                remove_table_entry(gi, table, entry)
                if args.delete or args.delete_links:
                    remove_files(entry[3], args.delete_links, ['.amb', '.ann', '.bwt', '.pac', '.sa'])
