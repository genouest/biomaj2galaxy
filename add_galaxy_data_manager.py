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
import configparser

from bioblend_contrib import galaxy


ADD_DBKEY_TOOL_ID = 'toolshed.genouest.org/repos/abretaud/data_manager_dbkeys/data_manager_dbkey/0.0.1' # This only creates a dbkey without any data associated to it
ADD_FASTA_TOOL_ID = 'toolshed.genouest.org/repos/abretaud/data_manager_fasta_dbkeys/data_manager_fasta_dbkeys/0.0.1'

ADD_BLAST_TOOL_ID = 'toolshed.genouest.org/repos/abretaud/data_manager_add_blastdb/data_manager_add_blastdb/0.0.1'
ADD_BOWTIE_TOOL_ID = 'toolshed.genouest.org/repos/abretaud/data_manager_add_bowtie/data_manager_add_bowtie/0.0.1'
ADD_BOWTIE2_TOOL_ID = 'toolshed.genouest.org/repos/abretaud/data_manager_add_bowtie2/data_manager_add_bowtie2/0.0.1'
ADD_BWA_TOOL_ID = 'toolshed.genouest.org/repos/abretaud/data_manager_add_bwa/data_manager_add_bwa/0.0.1'
ADD_2BIT_TOOL_ID = 'toolshed.genouest.org/repos/abretaud/data_manager_add_2bit/data_manager_add_2bit/0.0.1'

DEFAULT_SLEEP_TIME = 3

def get_dataset_state(gi, hda_id):
    dataset_info = gi.datasets.show_dataset(hda_id)

    return dataset_info['state']

def dataset_is_terminal(gi, hda_id):
    dataset_state = get_dataset_state(gi, hda_id)
    return dataset_state in [ 'ok', 'error' ]

def wait_completion(gi, fetch_res, args, sleep_time, exit_on_error=True):
    dataset_id = fetch_res['outputs'][0]['id']
    while fetch_res:
        if dataset_is_terminal( gi, dataset_id):
            fetch_res = None
        if fetch_res:
            time.sleep( sleep_time )

    dataset_info = gi.datasets.show_dataset(dataset_id)
    status = dataset_info['state']
    if exit_on_error and status == 'error':
        print >> sys.stderr, "ERROR: Job finished in error state! Aborting"
        print >> sys.stderr, "STDOUT content:"
        print >> sys.stderr, gi.datasets.show_stdout(dataset_id)
        print >> sys.stderr, "STDERR content:"
        print >> sys.stderr, gi.datasets.show_stderr(dataset_id)
        sys.exit(1)

def get_dbkey_entry(gi, dbkey):
    dbkeys = gi.tool_data.show_data_table('__dbkeys__')

    for k in dbkeys['fields']:
        if k[0] == dbkey:
            return k

def check_args(args):

    if not args.config and (not args.url or not args.api_key):
        print >> sys.stderr, "ERROR: --config or --url and --api-key options are required."
        sys.exit(1)

    if args.fasta_custom_sort_list and args.fasta_sorting_method != 'custom':
        args.fasta_custom_sort_list = ''

    if args.fasta_custom_sort_handling and args.fasta_sorting_method != 'custom':
        args.fasta_custom_sort_handling = ''

    if not args.genome_fasta and not args.fasta and not args.blastn and not args.blastp and not args.blastd and not args.bowtie and not args.bowtie2 and not args.bwa and not args.twobit:
        print >> sys.stderr, "ERROR: Nothing to do."
        sys.exit(1)

    if not args.no_file_check:
        if args.genome_fasta:
            args.genome_fasta = check_path(args.genome_fasta)
        if args.fasta:
            checked = []
            for f in args.fasta:
                checked += [check_path(f),]
            args.fasta = checked
        if args.blastn:
            checked = []
            for f in args.blastn:
                ok_path = check_path(f+".nin", f+".00.nin")
                if ok_path.endswith(".nin"):
                    ok_path = ok_path[:-4]
                elif ok_path.endswith(".00.nin"):
                    ok_path = ok_path[:-7]
                checked += [ok_path,]
            args.blastn = checked
        if args.blastp:
            checked = []
            for f in args.blastp:
                ok_path = check_path(f+".pin", f+".00.pin")
                if ok_path.endswith(".pin"):
                    ok_path = ok_path[:-4]
                elif ok_path.endswith(".00.pin"):
                    ok_path = ok_path[:-7]
                checked += [ok_path,]
            args.blastp = checked
        if args.blastd:
            checked = []
            for f in args.blastd:
                checked += [check_path(f+".rps")[:-4],]
            args.blastd = checked
        if args.bowtie:
            checked = []
            for f in args.bowtie:
                checked += [check_path(f+".1.ebwt")[:-7],]
            args.bowtie = checked
        if args.bowtie2:
            checked = []
            for f in args.bowtie2:
                checked += [check_path(f+".1.bt2")[:-6],]
            args.bowtie2 = checked
        if args.bwa:
            checked = []
            for f in args.bwa:
                checked += [check_path(f+".amb")[:-4],]
            args.bwa = checked
        if args.twobit:
            checked = []
            for f in args.twobit:
                checked += [check_path(f),]
            args.twobit = checked

    return args

def check_path(*files):
    for f in files:
        if os.path.isfile(f):
            return os.path.abspath(f)

    print >> sys.stderr, "ERROR: File '"+str(files)+"' could not be read!"
    sys.exit(1)

def need_dbkey(args):
    if args.fasta or args.genome_fasta:
        return True

    if args.bowtie or args.bowtie2 or args.bwa or args.twobit:
        return True

    return False

def get_display_names(paths, names, default_name):
    res_names = {}

    if not paths:
        return res_names

    i = 0
    for p in paths:
        if names and i < len(names):
            res_names[p] = names[i]
        else:
            if default_name:
                res_names[p] = default_name
            else:
                res_names[p] = os.path.basename(p)
        i += 1

    return res_names

def read_config(config_file):

    if not os.path.isfile(config_file):
        print >> sys.stderr, "ERROR: File '"+config_file+"' could not be read!"
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)
    if 'biomaj2galaxy' not in config:
        print >> sys.stderr, "ERROR: File '"+config_file+"' is malformed!"
        sys.exit(1)

    res = {}
    if 'apikey' in config['biomaj2galaxy']:
        res['apikey'] = config['biomaj2galaxy']['apikey']

    if 'url' in config['biomaj2galaxy']:
        res['url'] = config['biomaj2galaxy']['url']

    return res

if __name__ == '__main__':
    #Parse Command Line
    parser = argparse.ArgumentParser()
    parser.add_argument( '-c', '--config', help='Load options from config file')
    parser.add_argument( '-u', '--url', help='Url of the galaxy instance')
    parser.add_argument( '-k', '--api-key', help='Galaxy API key')
    parser.add_argument( '-d', '--dbkey', help='Dbkey to use (i.e. genome build like \'hg19\')')
    parser.add_argument( '-n', '--dbkey-display-name', help='Display name for the dbkey')
    parser.add_argument( '-g', '--genome-fasta', help='Path to a fasta file corresponding to a full reference genome. It will be used in visualizations for example.')
    parser.add_argument( '-f', '--fasta', help='Path to fasta file(s) that is/are not a full reference genome (space separated if multiple fasta files)', nargs='*')
    parser.add_argument( '-s', '--fasta-sorting-method', choices=['as_is', 'lexicographical', 'gatk', 'custom'], default='as_is', help='Method used for the sorting of fasta file(s)')
    parser.add_argument( '--fasta-custom-sort-list', help='Ordered comma separated list of sequence identifiers to use for sorting fasta file(s) (requires \'-s custom\' option)')
    parser.add_argument( '--fasta-custom-sort-handling', choices=['discard', 'keep_append', 'keep_prepend'], default='discard', help='How to handle non-specified identifiers (requires \'-s custom\' option)')
    parser.add_argument("--no-file-check", help="This option prevent the script from checking the source files existence.\nThis can be useful for files that are available on the web server running Galaxy, but not on the machine running this script.", action="store_true")

    # Index pregenerated
    parser.add_argument( '--blastn', help='Path(s) to pregenerated Blast nucleotide databank(s) (without file extension, space separated if multiple)', nargs='*') # doesn't need dbkey
    parser.add_argument( '--blastp', help='Path(s) to pregenerated Blast protein databank(s) (without file extension, space separated if multiple)', nargs='*') # doesn't need dbkey
    parser.add_argument( '--blastd', help='Path(s) to pregenerated Blast domain databank(s) (without file extension, space separated if multiple)', nargs='*') # doesn't need dbkey
    parser.add_argument( '--bowtie', help='Path(s) to pregenerated Bowtie index (without file extension, space separated if multiple)', nargs='*')
    parser.add_argument( '--bowtie2', help='Path(s) to pregenerated Bowtie2 index (without file extension, space separated if multiple)', nargs='*')
    parser.add_argument( '--bwa', help='Path(s) to pregenerated BWA index (without file extension, space separated if multiple)', nargs='*')
    parser.add_argument( '--twobit', help='Path(s) to pregenerated 2bit index (UCSC) (space separated if multiple)', nargs='*')

    parser.add_argument( '--genome-fasta-name', help='Display name for the full reference genome (default=--dbkey-display-name or --dbkey)')
    parser.add_argument( '--fasta-name', help='Display name(s) for fasta file, in the same order as --fasta options (default=--dbkey-display-name or --dbkey)', nargs='*')
    parser.add_argument( '--blastn-name', help='Display name(s) for pregenerated Blast nucleotide databank, in the same order as --blastn options (default=--dbkey-display-name or --dbkey)', nargs='*')
    parser.add_argument( '--blastp-name', help='Display name(s) for pregenerated Blast protein databank, in the same order as --blastp options (default=--dbkey-display-name or --dbkey)', nargs='*')
    parser.add_argument( '--blastd-name', help='Display name(s) for pregenerated Blast domain databank, in the same order as --blastd options (default=--dbkey-display-name or --dbkey)', nargs='*')
    parser.add_argument( '--bowtie-name', help='Display name(s) for pregenerated Blast nucleotide databank, in the same order as --bowtie options (default=--dbkey-display-name or --dbkey)', nargs='*')
    parser.add_argument( '--bowtie2-name', help='Display name(s) for pregenerated Blast nucleotide databank, in the same order as --bowtie2 options (default=--dbkey-display-name or --dbkey)', nargs='*')
    parser.add_argument( '--bwa-name', help='Display name(s) for pregenerated Blast nucleotide databank, in the same order as --bwa options (default=--dbkey-display-name or --dbkey)', nargs='*')
    parser.add_argument( '--twobit-name', help='Display name(s) for pregenerated Blast nucleotide databank, in the same order as --twobit options (default=--dbkey-display-name or --dbkey)', nargs='*')

    # TODO support other tables: tophat, tophat2, fasta_indexes

    args = parser.parse_args()

    args = check_args(args)

    config = {}
    if args.config:
        config = read_config(args.config)

    if "url" not in config:
        if not args.url:
            print >> sys.stderr, "ERROR: you must configure the galaxy server url (-c or -u option)"
            sys.exit(1)
        config['url'] = args.url

    if not config['url'].endswith('/'):
        config['url'] = config['url'] + "/"

    if "apikey" not in config:
        if not args.api_key:
            print >> sys.stderr, "ERROR: you must configure the galaxy server api key (-c or -k option)"
            sys.exit(1)
        config['apikey'] = args.api_key

    gi = galaxy.GalaxyContribInstance(url=config['url'], key=config['apikey'])

    dbkey_entry = get_dbkey_entry(gi, args.dbkey)
    has_dbkey = dbkey_entry != None
    create_dbkey = False
    if args.dbkey and not has_dbkey and need_dbkey(args):
        print "Need to create the dbkey '"+args.dbkey+"'"
        create_dbkey = True
    elif args.dbkey and has_dbkey:
        print "The dbkey '"+args.dbkey+"' already exists"
    elif not args.dbkey and need_dbkey(args):
        print >> sys.stderr, "ERROR: You must specify a dbkey to perform the action(s) you requested."
        sys.exit(1)
    elif not args.dbkey and not need_dbkey(args):
        print "No dbkey was specified, but it is not a problem as we don't need it."

    # Prepare a default display name that will be used if not specified in given args
    default_name = args.dbkey_display_name
    if not default_name and dbkey_entry:
        print "Trying to use dbkey_entry name: "+dbkey_entry[1]
        default_name = dbkey_entry[1]
    if not default_name:
        default_name = args.dbkey
    # get_display_names will use the filename if no default_name + no name defined in command lien

    genome_fasta_names = get_display_names([args.genome_fasta], [args.genome_fasta_name], default_name)
    fasta_names = get_display_names(args.fasta, args.fasta_name, default_name)
    blastn_names = get_display_names(args.blastn, args.blastn_name, default_name)
    blastp_names = get_display_names(args.blastp, args.blastp_name, default_name)
    blastd_names = get_display_names(args.blastd, args.blastd_name, default_name)
    bowtie_names = get_display_names(args.bowtie, args.bowtie_name, default_name)
    bowtie2_names = get_display_names(args.bowtie2, args.bowtie2_name, default_name)
    bwa_names = get_display_names(args.bwa, args.bwa_name, default_name)
    twobit_names = get_display_names(args.twobit, args.twobit_name, default_name)

    # Add the genome fasta if asked
    if args.genome_fasta:
        if not create_dbkey:
            # delete the existing dbkey to force the recomputing of len file
            print "Deleting the dbkey entry before recreating it (needed to recompute the len file)."
            ret = gi.tool_data.delete_data_table('__dbkeys__', "\t".join(dbkey_entry))
        # the dbkey is not (longer) existing: create it while adding the ref genome to force the computing of the len file
        print "Adding a new genome using fasta file '"+args.genome_fasta+"'"
        params = {}
        params['dbkey_source|dbkey_source_selector'] = 'new'
        params['dbkey_source|dbkey'] = args.dbkey
        params['dbkey_source|dbkey_name'] = default_name
        params['sequence_name'] = genome_fasta_names[args.genome_fasta]
        params['full_genome'] = True
        params['reference_source|reference_source_selector'] = 'directory'
        params['reference_source|fasta_filename'] = args.genome_fasta
        params['reference_source|create_symlink'] = 'true'
        params['sorting|sort_selector'] = args.fasta_sorting_method
        if args.fasta_sorting_method == 'custom':
            params['sorting|handle_not_listed|handle_not_listed_selector'] = args.fasta_custom_sort_handling
            n = 0
            for i in args.fasta_custom_sort_list.split(','):
                params['sorting|sequence_identifiers_'+n+'|identifier'] = i
                n += 1
        fetch_res = gi.tools.run_tool( None, ADD_FASTA_TOOL_ID, params )
        wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    elif create_dbkey: # Create the dbkey without ref genome (no len computing)
        print "Creating the dbkey '"+args.dbkey+"'"
        params = {}
        params['dbkey'] = args.dbkey
        params['dbkey_name']= default_name
        fetch_res = gi.tools.run_tool( None, ADD_DBKEY_TOOL_ID, params )
        wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    # Add the not-ref genomes or other fasta files (no .len will be computed)
    if args.fasta:
        for fasta in args.fasta:
            print "Adding a new fasta file '"+fasta+"'"
            params = {}
            params['dbkey_source|dbkey_source_selector'] = 'existing'
            params['dbkey_source|dbkey'] = args.dbkey
            params['sequence_name'] = fasta_names[fasta]
            params['full_genome'] = False
            params['reference_source|reference_source_selector'] = 'directory'
            params['reference_source|fasta_filename'] = fasta
            params['reference_source|create_symlink'] = 'true'
            params['sorting|sort_selector'] = args.fasta_sorting_method
            if args.fasta_sorting_method == 'custom':
                params['sorting|handle_not_listed|handle_not_listed_selector'] = args.fasta_custom_sort_handling
                n = 0
                for i in args.fasta_custom_sort_list.split(','):
                    params['sorting|sequence_identifiers_'+n+'|identifier'] = i
                    n += 1
            fetch_res = gi.tools.run_tool( None, ADD_FASTA_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    # Add blastn and blastp databanks
    if args.blastn:
        for blastn in args.blastn:
            print "Adding a new blastdb index '"+blastn+"'"
            params = {}
            if args.dbkey and len(args.blastn) > 1: # The id must be unique, only use dbkey if adding only one blastdb
                params['blastdb_id'] = args.dbkey
            else:
                params['blastdb_id'] = '' # Let it be generated
            params['blastdb_name'] = blastn_names[blastn]
            params['blastdb_path'] = blastn
            params['seq_type'] = 'blastdb'
            fetch_res = gi.tools.run_tool( None, ADD_BLAST_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    if args.blastp:
        for blastp in args.blastp:
            print "Adding a new blastdb_p index '"+blastp+"'"
            params = {}
            if args.dbkey and len(args.blastp) > 1: # The id must be unique, only use dbkey if adding only one blastdb
                params['blastdb_id'] = args.dbkey
            else:
                params['blastdb_id'] = '' # Let it be generated
            params['blastdb_name'] = blastp_names[blastp]
            params['blastdb_path'] = blastp
            params['seq_type'] = 'blastdb_p'
            fetch_res = gi.tools.run_tool( None, ADD_BLAST_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    if args.blastd:
        for blastd in args.blastd:
            print "Adding a new blastdb_d index '"+blastd+"'"
            params = {}
            if args.dbkey and len(args.blastd) > 1: # The id must be unique, only use dbkey if adding only one blastdb
                params['blastdb_id'] = args.dbkey
            else:
                params['blastdb_id'] = '' # Let it be generated
            params['blastdb_name'] = blastd_names[blastd]
            params['blastdb_path'] = blastd
            params['seq_type'] = 'blastdb_d'
            fetch_res = gi.tools.run_tool( None, ADD_BLAST_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    # Add BWA indexes
    if args.bwa:
        for bwa in args.bwa:
            print "Adding a new bwa index '"+bwa+"'"
            params = {}
            params['dbkey'] = args.dbkey
            params['index_id'] = '' # Let it be generated
            params['index_name'] = bwa_names[bwa]
            params['index_path'] = bwa
            fetch_res = gi.tools.run_tool( None, ADD_BWA_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    # Add Bowtie indexes
    if args.bowtie:
        for bowtie in args.bowtie:
            print "Adding a new bowtie index '"+bowtie+"'"
            params = {}
            params['dbkey'] = args.dbkey
            params['index_id'] = '' # Let it be generated
            params['index_name'] = bowtie_names[bowtie]
            params['index_path'] = bowtie
            fetch_res = gi.tools.run_tool( None, ADD_BOWTIE_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    # Add Bowtie2 indexes
    if args.bowtie2:
        for bowtie2 in args.bowtie2:
            print "Adding a new bowtie2 index '"+bowtie2+"'"
            params = {}
            params['dbkey'] = args.dbkey
            params['index_id'] = '' # Let it be generated
            params['index_name'] = bowtie2_names[bowtie2]
            params['index_path'] = bowtie2
            fetch_res = gi.tools.run_tool( None, ADD_BOWTIE2_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)

    # Add 2bit indexes
    if args.twobit:
        for twobit in args.twobit:
            print "Adding a new twobit index '"+twobit+"'"
            params = {}
            params['dbkey'] = args.dbkey
            params['index_path'] = twobit
            fetch_res = gi.tools.run_tool( None, ADD_2BIT_TOOL_ID, params )
            wait_completion(gi, fetch_res, args, DEFAULT_SLEEP_TIME)
