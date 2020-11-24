import os
import time
import uuid

from biomaj2galaxy import pass_context
from biomaj2galaxy.io import warn
from biomaj2galaxy.utils import check_input, get_dbkey_entry, wait_completion

import click


@click.command()
@click.argument("files", nargs=-1)
@click.option(
    "-d",
    "--dbkey",
    help="Dbkey to use (i.e. genome build like \'hg19\')",
    type=str
)
@click.option(
    "-n",
    "--dbkey-display-name",
    help="Display name for the dbkey (default=guessed from BioMAJ env vars, ie '${dbname} (${remoterelease})')",
    type=str
)
@click.option(
    "-g",
    "--genome-fasta",
    help="Path to a fasta file corresponding to a full reference genome. It will be used in visualizations for example.",
    type=str
)
@click.option(
    "--genome-fasta-name",
    help="Display name for the full reference genome (default=--dbkey-display-name or --dbkey)",
    type=str
)
@click.option(
    "-s",
    "--fasta-sorting-method",
    help="Method used for the sorting of genome fasta file",
    type=click.Choice(['as_is', 'lexicographical', 'gatk', 'custom']),
    default='as_is'
)
@click.option(
    "--fasta-custom-sort-list",
    help="Ordered comma separated list of sequence identifiers to use for sorting genome fasta file (requires \'-s custom\' option)",
    type=str
)
@click.option(
    "--fasta-custom-sort-handling",
    help="How to handle non-specified identifiers (requires \'-s custom\' option)",
    type=click.Choice(['discard', 'keep_append', 'keep_prepend']),
    default='discard'
)
@click.option(
    "--no-file-check",
    help="Don't check the source files existence.\nUseful for files that are available on the Galaxy server, but not on the machine running this script.",
    is_flag=True
)
@click.option(
    "--star-with-gtf",
    help="STAR indices were made with an annotation (i.e., --sjdbGTFfile and --sjdbOverhang were used).",
    is_flag=True
)
@click.option(
    "--star-version",
    help="Version of STAR used to create the index (default: none)",
    type=str
)
@click.option(
    "--no-biomaj-env",
    help="Add this flag if you don't want biomaj2galaxy to use BioMAJ env variables to guess file names.",
    is_flag=True
)
@pass_context
def add(ctx, files, dbkey, dbkey_display_name, genome_fasta, genome_fasta_name, fasta_sorting_method, fasta_custom_sort_list, fasta_custom_sort_handling, no_file_check, star_with_gtf, star_version, no_biomaj_env):
    """Add data to a Galaxy data table. FILES is a list of path respecting this syntax: data_table_name:/path/to/data:Data name (e.g. "bowtie2:/db/some/where/my_genome:My supercool genome"). You can escape ':' by writing '\\:'"""

    ADD_FASTA_TOOL_ID = 'toolshed.g2.bx.psu.edu/repos/devteam/data_manager_fetch_genome_dbkeys_all_fasta/data_manager_fetch_genome_all_fasta_dbkey/0.0.4'
    DM_MANUAL_TOOL_ID = 'toolshed.g2.bx.psu.edu/repos/iuc/data_manager_manual/data_manager_manual/0.0.2'

    # Fetch the list of known tables with their columns
    tables_format = {}
    tables = ctx.gi.tool_data.get_data_tables()
    for t in tables:
        tables_format[t['name']] = ctx.gi.tool_data.show_data_table(t['name'])['columns']

        # A stupid fix for the twobit table which for some unknown reason doesn't have a 'name' column_name
        # As this 'name' column is required for a data table, the galaxy code adds a non-existing one when it is not found in the table defintion.
        if t['name'] == 'twobit' and 'name' in tables_format[t['name']]:
            tables_format[t['name']].remove('name')

    # Define some simpler synonyms for data tables
    data_table_synonyms = {
        'fasta': 'all_fasta',
        'bowtie': 'bowtie_indexes',
        'bowtie2': 'bowtie2_indexes',
        'bwa': 'bwa_indexes',
        'bwa_mem': 'bwa_mem_indexes',
        'tophat2': 'tophat2_indexes',
        'star': 'rnastar_index2x_versioned',
    }

    files_info = []
    for f in files:
        f = f.replace("\\:", '___colon___')
        f_info = f.split(':')
        f_info = [x.replace('___colon___', ':') for x in f_info]

        if len(f_info) < 2 or len(f_info) > 3:
            raise Exception('Malformed file information "%s"' % f_info)

        if f_info[0] not in tables_format:
            if f_info[0] in data_table_synonyms:
                f_info[0] = data_table_synonyms[f_info[0]]
            else:
                raise Exception('Unknown data table name "%s"' % f_info[0])

        f_info[1] = check_input([f_info[1]], check_existence=(not no_file_check), use_biomaj_env=(not no_biomaj_env))[0]

        if len(f_info) == 3:
            files_info.append({'table': f_info[0], 'path': f_info[1], 'name': f_info[2]})
        else:
            files_info.append({'table': f_info[0], 'path': f_info[1]})

    # Check which tables we're touching
    table_counts = {}
    for f_info in files_info:
        if f_info['table'] not in table_counts:
            table_counts[f_info['table']] = 0

        table_counts[f_info['table']] += 1

    # Verify dbkey
    dbkey_entry = get_dbkey_entry(ctx.gi, dbkey)
    dbkey_exists = dbkey_entry is not None

    need_dbkey = genome_fasta or (len(table_counts) == 0)
    for c in table_counts.keys():
        need_dbkey = 'dbkey' in tables_format[c]
        if need_dbkey:
            break

    create_dbkey = dbkey and not dbkey_exists and need_dbkey

    if create_dbkey:
        print("Need to create the dbkey '" + dbkey + "'")
    elif dbkey and dbkey_exists:
        print("The dbkey '" + dbkey + "' already exists")
    elif not dbkey and not need_dbkey:
        print("No dbkey was specified, but it is not a problem as we don't need it.")
    elif not dbkey and need_dbkey:
        raise Exception("ERROR: You must specify a dbkey to perform the action(s) you requested.")

    # Prepare a default display name that will be used if not specified
    if not dbkey_display_name:
        if 'dbname' in os.environ and 'remoterelease' in os.environ:
            dbkey_display_name = "%s (%s)" % (os.environ['dbname'], os.environ['remoterelease'])

    default_name = dbkey_display_name
    if not default_name and dbkey_entry:
        print("Trying to use dbkey_entry name: " + dbkey_entry[1])
        default_name = dbkey_entry[1]
    if not default_name:
        default_name = dbkey

    for f_info in files_info:
        if 'name' not in f_info:
            if not default_name:
                f_info['name'] = os.path.basename(f_info['path'])
            else:
                f_info['name'] = default_name

    # Add the genome fasta if asked
    if genome_fasta:
        if not create_dbkey:
            # delete the existing dbkey to force the recomputing of len file
            print("Deleting the dbkey entry before recreating it (needed to recompute the len file).")
            ctx.gi.tool_data.delete_data_table('__dbkeys__', "\t".join(dbkey_entry))

        if not genome_fasta_name:
            genome_fasta_name = default_name

        genome_fasta_abs = check_input([genome_fasta], check_existence=(not no_file_check), use_biomaj_env=(not no_biomaj_env))[0]

        # the dbkey is not (or not longer) existing: create it while adding the ref genome to force the computing of the len file
        print("Adding a new genome using fasta file '%s' -> '%s'" % (genome_fasta_name, genome_fasta_abs))
        params = {}
        params['dbkey_source|dbkey_source_selector'] = 'new'
        params['dbkey_source|dbkey'] = dbkey
        params['dbkey_source|dbkey_name'] = default_name
        params['sequence_name'] = genome_fasta_name
        params['reference_source|reference_source_selector'] = 'directory'
        params['reference_source|fasta_filename'] = genome_fasta_abs
        params['reference_source|create_symlink'] = 'true'
        params['sorting|sort_selector'] = fasta_sorting_method
        if fasta_sorting_method == 'custom':
            params['sorting|handle_not_listed|handle_not_listed_selector'] = fasta_custom_sort_handling
            n = 0
            for i in fasta_custom_sort_list.split(','):
                params['sorting|sequence_identifiers_' + n + '|identifier'] = i
                n += 1
        fetch_res = ctx.gi.tools.run_tool(None, ADD_FASTA_TOOL_ID, params)
        datasetid = fetch_res['outputs'][0]['id']
        jobid = None
        if 'jobs' in fetch_res:
            jobid = fetch_res['jobs'][0]['id']
        wait_completion(ctx.gi, datasetid, jobid)

    elif create_dbkey:  # Create the dbkey without ref genome (no len computing)
        print("Will create the dbkey '" + dbkey + "'")
        files_info.append({'table': '__dbkeys__', 'name': dbkey_display_name})
        table_counts['__dbkeys__'] = 1

    # Now add all associated data
    manual_dm_params = {}
    index_entry = 0
    for f_info in files_info:

        if 'path' in f_info:
            print("Adding a new entry to table '%s': '%s' -> '%s'" % (f_info['table'], f_info['name'], f_info['path']))
        else:
            print("Adding a new entry to table '%s': '%s' -> No path" % (f_info['table'], f_info['name']))

        vals = {
            'dbkey': dbkey,
            'name': f_info['name'],
            'path': f_info['path'] if 'path' in f_info else '',
            'db_path': f_info['path'] if 'path' in f_info else '',  # diamond data table
            'url': f_info['path'] if 'path' in f_info else '',
            'with-gtf': '1' if star_with_gtf else '0',  # rnastar data table, old data table
            'with_gene_model': '1' if star_with_gtf else '0',  # rnastar data table, recent data table
            'version': star_version if star_version else '0',  # rnastar data table, recent data table
            'len_path': f_info['path'] if 'path' in f_info else '',  # __dbkeys__data table
        }

        if dbkey and table_counts[f_info['table']] == 1:  # The id must be unique, only use dbkey if adding only one blastdb
            vals['value'] = dbkey
        else:
            vals['value'] = dbkey + "_" + str(uuid.uuid4())  # Let it be generated

        col_index = 0
        for col in tables_format[f_info['table']]:
            if col not in vals:
                warn("Skipping unknown column named '%s' in table '%s'." % (col, f_info['table']))

            manual_dm_params['data_tables_%s|columns_%s|data_table_column_name' % (index_entry, col_index)] = col
            manual_dm_params['data_tables_%s|columns_%s|data_table_column_value' % (index_entry, col_index)] = vals[col]
            manual_dm_params['data_tables_%s|columns_%s|is_path|is_path_selector' % (index_entry, col_index)] = 'no'
            col_index += 1

        manual_dm_params['data_tables_%s|data_table_name' % (index_entry)] = f_info['table']
        index_entry += 1

    fetch_res = ctx.gi.tools.run_tool(None, DM_MANUAL_TOOL_ID, manual_dm_params)
    datasetid = fetch_res['outputs'][0]['id']
    jobid = None
    if 'jobs' in fetch_res:
        jobid = fetch_res['jobs'][0]['id']
    wait_completion(ctx.gi, datasetid, jobid)

    # Reload all tables just in case
    time.sleep(1)  # Reloading too soon might not work for some strange reason
    for table in table_counts:
        print("Reloading table '%s'" % table)
        ctx.gi.tool_data.reload_data_table(table)
