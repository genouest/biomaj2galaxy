import time

from biomaj2galaxy import pass_context

import click


@click.command()
@click.argument("dbkey", type=str)
@click.argument("tables", nargs=-1)
@click.option(
    "--exact",
    help="Remove only exact matches instead of removing all lines with an id beginning with the given dbkey.",
    is_flag=True
)
@pass_context
def rm(ctx, dbkey, tables, exact):
    """Remove data from Galaxy data tables, where DBKEY is the id of the data to remove, and TABLES is an optional list of tables to remove data from (by default, data will be removed in all tables)."""

    # Define some simpler synonyms for data tables
    data_table_synonyms = {
        'fasta': 'all_fasta',
        'bowtie': 'bowtie_indexes',
        'bowtie2': 'bowtie2_indexes',
        'bwa': 'bwa_indexes',
        'bwa_mem': 'bwa_mem_indexes',
        'tophat2': 'tophat2_indexes',
    }

    # Fetch the list of known tables with their columns
    tables_format = {}
    tables_entries = {}
    online_tables = ctx.gi.tool_data.get_data_tables()
    for t in online_tables:
        content = ctx.gi.tool_data.show_data_table(t['name'])
        tables_format[t['name']] = content['columns']
        tables_entries[t['name']] = content['fields']

    tables_to_clean = []
    if tables:
        for table in tables:
            if table in data_table_synonyms:
                table = data_table_synonyms[table]

            if table in tables_format:
                tables_to_clean.append(table)
            else:
                raise Exception('Unknown data table name "%s"' % table)
    else:
        tables_to_clean = tables_format.keys()

    print("Will remove '%s' entries from tables: \n%s" % (dbkey, ', '.join(tables_to_clean)))

    # Always delete from the __dbkeys__ table
    table = '__dbkeys__'
    if 'value' in tables_format[table]:
        dbkey_field = tables_format[table].index('value')

        for line in tables_entries[table]:
            if line[dbkey_field] == dbkey:
                print("Deleting from '" + table + "' table")
                ctx.gi.tool_data.delete_data_table(table, "\t".join(line))

    # Remove from asked tables
    for table in tables_to_clean:
        if 'dbkey' in tables_format[table]:
            dbkey_field = tables_format[table].index('dbkey')
        elif 'value' in tables_format[table]:
            dbkey_field = tables_format[table].index('value')
        else:
            continue

        for line in tables_entries[table]:
            if len(line) > dbkey_field:  # Sometimes Galaxy is lying (featurecounts_anno table)
                if (exact and line[dbkey_field] == dbkey) or (not exact and line[dbkey_field].startswith(dbkey)):
                    print("Deleting from '" + table + "' table")
                    ctx.gi.tool_data.delete_data_table(table, "\t".join(line))

    # Reload all tables just in case
    time.sleep(1)  # Reloading too soon might not work for some strange reason
    print("Reloading tables")
    for table in tables_to_clean:
        ctx.gi.tool_data.reload_data_table(table)
    print("Done")
