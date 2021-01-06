# BioMAJ2Galaxy

[![Lint and test](https://github.com/genouest/biomaj2galaxy/workflows/Lint%20and%20test/badge.svg)](https://github.com/genouest/biomaj2galaxy/actions)

## About

With this python module you can perform the following actions on a Galaxy server:

* Add new items to data libraries
* Remove items from data libraries
* Add new items to tool data tables using data managers
* Remove items from tool data tables

These scripts are primarily designed to be used as BioMAJ (http://biomaj.genouest.org) post processes,
but they can probably used directly from the command line if you need to.

This work has been published in GigaScience:

[BioMAJ2Galaxy: automatic update of reference data in Galaxy using BioMAJ.
Bretaudeau A, Monjeaud C, Le Bras Y, Legeai F, Collin O.
Gigascience. 2015 May 9;4:22. doi: 10.1186/s13742-015-0063-8. eCollection 2015.](https://dx.doi.org/10.1186%2Fs13742-015-0063-8)

## Installation

In most cases, you can install it easily with:

```bash
$ pip install biomaj2galaxy

# On first use you'll need to create a config file to connect to the Galaxy server, just run:
$ biomaj2galaxy init
Welcome to BioMAJ2Galaxy
url: http://localhost/
apikey: your-api-key
```

You need an API key to access your galaxy server. You need to use one from an admin account.

`allow_library_path_paste` should be set in `config/galaxy.yml` (or `config/galaxy.ini` for older versions)

Finally, if you want to add or remove items from tool data tables, you will need to install two data managers from the ToolShed:

 - `data_manager_manual` by the user `iuc`
 - `data_manager_fetch_genome_dbkeys_all_fasta` by the user `devteam`

## Usage

To see how to use each script (not necessarily from BioMAJ), just launch it with --help option.

Here is an example post-process and remove process configuration for BioMAJ, using data manager:

```
B1.db.post.process=GALAXY
GALAXY=galaxy_dm

galaxy_dm.name=galaxy_dm
galaxy_dm.desc=Add files to Galaxy tool data tables
galaxy_dm.type=galaxy
galaxy_dm.exe=biomaj2galaxy
galaxy_dm.args=add -d "${localrelease}" -g fasta/all.fa bowtie2:bowtie2/all "blastdb:blast/Homo_sapiens-proteins:Homo sapiens proteins"

db.remove.process=RM_GALAXY
RM_GALAXY=rm_galaxy_dm

rm_galaxy_dm.name=rm_galaxy_dm
rm_galaxy_dm.desc=Remove from Galaxy tool data tables
rm_galaxy_dm.type=galaxy
rm_galaxy_dm.exe=biomaj2galaxy
rm_galaxy_dm.args=rm "${db.name}-${removedrelease}"
```

And the same using data libraries:

```
B2.db.post.process=GALAXY
GALAXY=galaxy_dl

galaxy_dl.name=galaxy_dl
galaxy_dl.desc=Add files to Galaxy data libraries
galaxy_dl.type=galaxy
galaxy_dl.exe=biomaj2galaxy
galaxy_dl.args=add_lib -l "Homo sapiens genome (${remoterelease})" --lib-desc "Genome of Homo sapiens (version ${remoterelease}) downloaded from NCBI" -f "${localrelease}" --replace fasta/all.fa

db.remove.process=RM_GALAXY
RM_GALAXY=rm_galaxy_dl

rm_galaxy_dl.name=rm_galaxy_dl
rm_galaxy_dl.desc=Remove from Galaxy data libraries
rm_galaxy_dl.type=galaxy
rm_galaxy_dl.exe=biomaj2galaxy
rm_galaxy_dl.args=rm_lib -f "${db.name}-${removedrelease}" "Homo sapiens genome (${remote.release})"
```

By default, relative file paths will be interpreted as relative to `${data.dir}/${dir.version}/${localrelease}` if these envionment variables are set. This can be disabled by using the --no-biomaj-env option.

## Changes

- 2.2.0
    - Fixed errors with Galaxy 20.05

- 2.1.0
    - Fixed errors with Galaxy >19.05 (also fixes in Galaxy: https://github.com/galaxyproject/galaxy/issues/8792 and in IUC: https://github.com/galaxyproject/tools-iuc/pull/2634)

- 2.0.1
    - Fixed error with Galaxy 18.09 (also fixed in Galaxy: https://github.com/galaxyproject/galaxy/issues/7048)
    - Fixed error while waiting for job completion

- 2.0
    - Complete rewrite using data_manager_manual
