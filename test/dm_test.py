import logging
import os
import time
import unittest

from biomaj2galaxy.cli import biomaj2galaxy

from click.testing import CliRunner

from . import gi


class DmTest(unittest.TestCase):

    def test_add_dbkey(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check'], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

    def test_add_bowtie2(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'bowtie2:/some/path/foo/bar'], catch_exceptions=False)

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        assert [new_dbkey, new_dbkey, new_dbkey_name, '/some/path/foo/bar'] in bowtie2

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

    def test_add_genome(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', '-g', '/data/sample.fasta'], catch_exceptions=False)

        fasta = self.gi.tool_data.show_data_table('all_fasta')
        fasta = fasta['fields']
        assert [new_dbkey, new_dbkey, new_dbkey_name, '/galaxy-central/tool-data/test_dbkey/seq/test_dbkey.fa'] in fasta

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, '/galaxy-central/tool-data/test_dbkey/len/test_dbkey.len'] in dbkeys

    def test_add_bowtie2_multiple(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'bowtie2:/some/path/foo/bar', 'bowtie2:/some/other_path/foo/bar', 'bowtie2:/some/really/other/path/foo/bar:With a cool name'], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        uuids = [x[0] for x in bowtie2]
        bowtie2 = [x[1:] for x in bowtie2]
        assert [new_dbkey, new_dbkey_name, '/some/path/foo/bar'] in bowtie2
        assert [new_dbkey, new_dbkey_name, '/some/other_path/foo/bar'] in bowtie2
        assert [new_dbkey, "With a cool name", '/some/really/other/path/foo/bar'] in bowtie2

        for u in uuids:
            assert u.startswith(new_dbkey)

    def test_add_mess(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'bowtie2:/some/path/foo/bar', 'bowtie2:/some/other_path/foo/bar', 'bowtie2:/some/really/other/path/foo/bar:With a cool name', 'blastdb:/foo/really/other/path/foo/bar:With a cool name too!', 'blastdb:/foo/really/other/xxxx/bar:Wisuith a cool name too!', 'bwa:/foo/really/foo/bar:With a cool name too bwa!', 'twobit:/foo/really/foo/bar:Wblablatoo!', 'star:/foo/bloup/test/faa/bor:Wixxxtoo!', 'fasta:/fxx/bloup/txx/faa/bor:Wixxx fasta too!'], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        uuids = [x[0] for x in bowtie2]
        bowtie2 = [x[1:] for x in bowtie2]
        assert [new_dbkey, new_dbkey_name, '/some/path/foo/bar'] in bowtie2
        assert [new_dbkey, new_dbkey_name, '/some/other_path/foo/bar'] in bowtie2
        assert [new_dbkey, "With a cool name", '/some/really/other/path/foo/bar'] in bowtie2

        for u in uuids:
            assert u.startswith(new_dbkey) and u != new_dbkey

        blastdb = self.gi.tool_data.show_data_table('blastdb')
        blastdb = blastdb['fields']
        uuids = [x[0] for x in blastdb]
        blastdb = [x[1:] for x in blastdb]
        assert ['With a cool name too!', '/foo/really/other/path/foo/bar'] in blastdb
        assert ["Wisuith a cool name too!", '/foo/really/other/xxxx/bar'] in blastdb

        for u in uuids:
            assert u.startswith(new_dbkey) and u != new_dbkey

        bwa = self.gi.tool_data.show_data_table('bwa_indexes')
        bwa = bwa['fields']
        assert [new_dbkey, new_dbkey, 'With a cool name too bwa!', '/foo/really/foo/bar'] in bwa

        twobit = self.gi.tool_data.show_data_table('twobit')
        twobit = twobit['fields']
        assert [new_dbkey, '/foo/really/foo/bar'] in twobit

        star = self.gi.tool_data.show_data_table('rnastar_index2x_versioned')
        star = star['fields']
        assert [new_dbkey, new_dbkey, 'Wixxxtoo!', '/foo/bloup/test/faa/bor', '0', '0'] in star

        fasta = self.gi.tool_data.show_data_table('all_fasta')
        fasta = fasta['fields']
        assert [new_dbkey, new_dbkey, 'Wixxx fasta too!', '/fxx/bloup/txx/faa/bor'] in fasta

    def test_add_star_gtf(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'star:/foo/bloup/test/faa/bor:Wixxxtoo!', '--star-with-gtf'], catch_exceptions=False)

        star = self.gi.tool_data.show_data_table('rnastar_index2x_versioned')
        star = star['fields']
        assert [new_dbkey, new_dbkey, 'Wixxxtoo!', '/foo/bloup/test/faa/bor', '1', '0'] in star

    def test_add_star_gtf_version(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'star:/foo/bloup/test/faa/bor:Wixxxtoo!', '--star-with-gtf', '--star-version', '1.7.6'], catch_exceptions=False)

        star = self.gi.tool_data.show_data_table('rnastar_index2x_versioned')
        star = star['fields']
        assert [new_dbkey, new_dbkey, 'Wixxxtoo!', '/foo/bloup/test/faa/bor', '1', '1.7.6'] in star

    def test_add_biomaj_env(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'Cool_db (v3.0)'

        back_env = os.environ
        os.environ['dbname'] = "Cool_db"
        os.environ['remoterelease'] = "v3.0"
        os.environ['data.dir'] = "/db/"
        os.environ['dirversion'] = "some/dir"
        os.environ['localrelease'] = "v3.0beta"

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--no-file-check', 'bowtie2:foo/bar'], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        assert [new_dbkey, new_dbkey, new_dbkey_name, '/db/some/dir/v3.0beta/foo/bar'] in bowtie2

        os.environ = back_env

    def test_rm_bowtie2(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'bowtie2:/some/path/foo/bar'], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        assert [new_dbkey, new_dbkey, new_dbkey_name, '/some/path/foo/bar'] in bowtie2

        runner.invoke(biomaj2galaxy, ['rm', new_dbkey], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] not in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        assert [new_dbkey, new_dbkey, new_dbkey_name, '/some/path/foo/bar'] not in bowtie2

    def test_rm_multiple(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'bowtie2:/some/path/foo/bar', 'bowtie2:/some/other_path/foo/bar', 'bowtie2:/some/really/other/path/foo/bar:With a cool name'], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        uuids = [x[0] for x in bowtie2]
        bowtie2 = [x[1:] for x in bowtie2]
        assert [new_dbkey, new_dbkey_name, '/some/path/foo/bar'] in bowtie2
        assert [new_dbkey, new_dbkey_name, '/some/other_path/foo/bar'] in bowtie2
        assert [new_dbkey, "With a cool name", '/some/really/other/path/foo/bar'] in bowtie2

        for u in uuids:
            assert u.startswith(new_dbkey)

        runner.invoke(biomaj2galaxy, ['rm', new_dbkey], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] not in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        uuids = [x[0] for x in bowtie2]
        bowtie2 = [x[1:] for x in bowtie2]
        assert [new_dbkey, new_dbkey_name, '/some/path/foo/bar'] not in bowtie2
        assert [new_dbkey, new_dbkey_name, '/some/other_path/foo/bar'] not in bowtie2
        assert [new_dbkey, "With a cool name", '/some/really/other/path/foo/bar'] not in bowtie2

        for u in uuids:
            assert not u.startswith(new_dbkey)

    def test_rm_multiple_exact(self):

        new_dbkey = 'test_dbkey'
        new_dbkey_name = 'My cool dbkey'

        runner = CliRunner()
        runner.invoke(biomaj2galaxy, ['add', '--dbkey', new_dbkey, '--dbkey-display-name', new_dbkey_name, '--no-file-check', 'bowtie2:/some/path/foo/bar', 'bowtie2:/some/other_path/foo/bar', 'bowtie2:/some/really/other/path/foo/bar:With a cool name'], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        uuids = [x[0] for x in bowtie2]
        bowtie2 = [x[1:] for x in bowtie2]
        assert [new_dbkey, new_dbkey_name, '/some/path/foo/bar'] in bowtie2
        assert [new_dbkey, new_dbkey_name, '/some/other_path/foo/bar'] in bowtie2
        assert [new_dbkey, "With a cool name", '/some/really/other/path/foo/bar'] in bowtie2

        for u in uuids:
            assert u.startswith(new_dbkey)

        runner.invoke(biomaj2galaxy, ['rm', '--exact', new_dbkey], catch_exceptions=False)

        dbkeys = self.gi.tool_data.show_data_table('__dbkeys__')
        dbkeys = dbkeys['fields']
        assert [new_dbkey, new_dbkey_name, ''] not in dbkeys

        bowtie2 = self.gi.tool_data.show_data_table('bowtie2_indexes')
        bowtie2 = bowtie2['fields']
        uuids = [x[0] for x in bowtie2]
        bowtie2 = [x[1:] for x in bowtie2]
        assert [new_dbkey, new_dbkey_name, '/some/path/foo/bar'] not in bowtie2
        assert [new_dbkey, new_dbkey_name, '/some/other_path/foo/bar'] not in bowtie2
        assert [new_dbkey, "With a cool name", '/some/really/other/path/foo/bar'] not in bowtie2

        for u in uuids:
            assert u.startswith(new_dbkey) and u != new_dbkey

    def setUp(self):
        self.gi = gi

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("bioblend").setLevel(logging.WARNING)

        # Empty all tables
        touched_tables = [
            'bowtie2_indexes',
            'blastdb',
            'twobit',
            '__dbkeys__',
            'rnastar_index2x_versioned',
            'bwa_indexes',
            'all_fasta'
        ]
        tables = [x['name'] for x in self.gi.tool_data.get_data_tables()]
        for table in tables:
            if table in touched_tables:  # To speed things up a bit
                fields = self.gi.tool_data.show_data_table(table)['fields']
                for line in fields:
                    self.gi.tool_data.delete_data_table(table, "\t".join(line))
                time.sleep(1)  # Reloading too soon might not work for some strange reason
                self.gi.tool_data.reload_data_table(table)

    def tearDown(self):
        # Empty all tables
        touched_tables = [
            'bowtie2_indexes',
            'blastdb',
            'twobit',
            '__dbkeys__',
            'rnastar_index2x_versioned',
            'bwa_indexes',
            'all_fasta'
        ]
        tables = [x['name'] for x in self.gi.tool_data.get_data_tables()]
        for table in tables:
            if table in touched_tables:  # To speed things up a bit
                fields = self.gi.tool_data.show_data_table(table)['fields']
                for line in fields:
                    self.gi.tool_data.delete_data_table(table, "\t".join(line))
                time.sleep(1)  # Reloading too soon might not work for some strange reason
                self.gi.tool_data.reload_data_table(table)
