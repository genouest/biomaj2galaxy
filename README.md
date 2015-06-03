=============
BioMAJ2Galaxy
=============

About
=====

With these python scripts you can perform the following actions on a Galaxy server:

    * Add new items to data libraries
    * Remove items from data libraries
    * Add new items to tool data tables using data managers
    * Remove items from tool data tables

These scripts are primarily designed to be used as BioMAJ (http://biomaj.genouest.org) post processes,
but they can probably used directly from the command line if you need to.

This work has been published in GigaScience:

BioMAJ2Galaxy: automatic update of reference data in Galaxy using BioMAJ.
Bretaudeau A, Monjeaud C, Le Bras Y, Legeai F, Collin O.
Gigascience. 2015 May 9;4:22. doi: 10.1186/s13742-015-0063-8. eCollection 2015.

Licence
=======

Author: Anthony Bretaudeau <anthony.bretaudeau@rennes.inra.fr>

This software is governed by the CeCILL license under French law and
abiding by the rules of distribution of free software.  You can  use, 
modify and/ or redistribute the software under the terms of the CeCILL
license as circulated by CEA, CNRS and INRIA at the following URL
"http://www.cecill.info".

As a counterpart to the access to the source code and  rights to copy,
modify and redistribute granted by the license, users are provided only
with a limited warranty  and the software's author,  the holder of the
economic rights,  and the successive licensors  have only  limited
liability. 

In this respect, the user's attention is drawn to the risks associated
with loading,  using,  modifying and/or developing or reproducing the
software by the user in light of its specific status of free software,
that may mean  that it is complicated to manipulate,  and  that  also
therefore means  that it is reserved for developers  and  experienced
professionals having in-depth computer knowledge. Users are therefore
encouraged to load and test the software's suitability as regards their
requirements in conditions enabling the security of their systems and/or 
data to be ensured and,  more generally, to use and operate it in the 
same conditions as regards security. 

The fact that you are presently reading this means that you have had
knowledge of the CeCILL license and that you accept its terms.

Requirements
============

These script requires the BioBlend (https://github.com/afgane/bioblend) python library to interact with Galaxy server.

In most cases, you can install it easily with:

    pip install bioblend

The bioblend_contrib directory contains some code to extend the BioBlend library. This code has been merged to the official github repository, it will be available out of the box in the next stable release.

A recent version of Galaxy is required: the last code changes were committed on 2015-01-26, any posterior stable version should work. 

You need an API key to access your galaxy server. You need to use one from an admin account. The master API key defined in config/galaxy.ini doesn't work at the time of writing this doc (2014-10-13).

allow_library_path_paste should be set in config/galaxy.ini

Finally, if you want to add or remove items from tool data tables (add_galaxy_data_manager.py and remove_galaxy_data_manager.py), you will need to install some data managers.
First configure your Galaxy server to access the Galaxy User Group Grand Ouest (GUGGO) Tool Shed: open config/tool_sheds_conf.xml and add this line:

    <tool_shed name="GenOuest main tool shed" url="http://toolshed.genouest.org/"/>

Then install all the tools in the "Data manager" category of this Tool Shed. Briefly, there is one for each currently supported file format (2bit, blastdb, bowtie, bowtie2, bwa), one to only create a dbkey (when you want to add a genome without a corresponding fasta file) and one for fasta format. The script add_galaxy_data_manager.py automatically uses the right data manager depending on the option you give it on the command line.

Usage
=====

To see how to use each script (not necessarily from BioMAJ), just launch it with --help option.

Here is an example post-process and remove process configuration for BioMAJ, using data manager:

    B1.db.post.process=GALAXY
    GALAXY=galaxy_dm

    galaxy_dm.name=galaxy_dm
    galaxy_dm.desc=Add files to Galaxy tool data tables
    galaxy_dm.type=galaxy
    galaxy_dm.exe=add_galaxy_data_manager.py
    galaxy_dm.args=-u http://example.org/galaxy/ -k my_api_key -d "${localrelease}" -n "Homo sapiens (${remoterelease})" -g ${data.dir}/${dir.version}/${localrelease}/fasta/all.fa --bowtie2 ${datadir}/${dir.version}/${localrelease}/bowtie/all --blastn ${data.dir}/${dir.version}/${localrelease}/blast/Homo_sapiens-ncbi_testing

    db.remove.process=RM_GALAXY
    RM_GALAXY=rm_galaxy_dm

    rm_galaxy_dm.name=rm_galaxy_dm
    rm_galaxy_dm.desc=Remove from Galaxy tool data tables
    rm_galaxy_dm.type=galaxy
    rm_galaxy_dm.exe=remove_galaxy_data_manager.py
    rm_galaxy_dm.args=-u http://example.org/galaxy/ -k my_api_key -d "${db.name}-${removedrelease}" -f --blastn --bowtie2 --delete-len

Note that the --delete-len option is only useful if the path to the *.len files (inside Galaxy tree) is accessible from the machine running BioMAJ.

And the same using data libraries:

    B2.db.post.process=GALAXY
    GALAXY=galaxy_dl

    galaxy_dl.name=galaxy_dl
    galaxy_dl.desc=Add files to Galaxy data libraries
    galaxy_dl.type=galaxy
    galaxy_dl.exe=add_galaxy_library.py
    galaxy_dl.args=-u http://example.org/galaxy/ -k my_api_key -l "Homo sapiens genome (${remoterelease})" --lib-desc "Genome of Homo sapiens (version ${remoterelease}) downloaded from NCBI" -f "${localrelease}" --replace ${data.dir}/${dir.version}/${localrelease}/fasta/all.fa

    db.remove.process=RM_GALAXY
    RM_GALAXY=rm_galaxy_dl

    rm_galaxy_dl.name=rm_galaxy_dl
    rm_galaxy_dl.desc=Remove from Galaxy data libraries
    rm_galaxy_dl.type=galaxy
    rm_galaxy_dl.exe=remove_galaxy_library.py
    rm_galaxy_dl.args=-u http://example.org/galaxy/ -k my_api_key -l "Homo sapiens genome (${remote.release})" -f "${db.name}-${removedrelease}"


Loading url and api key from a config file
==========================================

If you don't want to write your Galaxy url or api key in the command line, you can write these parameters in a config file.
Create a file looking like this:

    [biomaj2galaxy]
    url=http://example.org/galaxy/
    apikey=my_api_key

You can then replace the following options in the command lines:

    -u http://example.org/galaxy/ -k my_api_key

By this single option:

    -c your_config_file.ini

-u and -k options are overriden by the content of the config file

TODO
====

    * There is no way yet to remove from disk multi-volume blast databanks when using remove_galaxy_data_manager.py
    
    * Make it possible to use the future BioMAJ new REST API instead of using post processes
    
    * Contribute code to bioblend: done, https://github.com/afgane/bioblend/pull/105
    * Trackster visualizations do not read genome list from data tables: done, PR #601
    * Wrong list in upload form: done, PR #601
    
    * The blastdb and blastdb_p data tables are not currently used by the blast+ tools from the following repository: http://toolshed.g2.bx.psu.edu/view/devteam/ncbi_blast_plus (See https://github.com/peterjc/galaxy_blast/issues/22  and https://github.com/peterjc/galaxy_blast/issues/52 for more info)
    Until the wrappers are updated, you can manually modify the file ncbi_blast_plus/tools/ncbi_blast_plus/ncbi_macros.xml and replace the blocks that look like this:
    
        <options from_file="blastdb.loc">
            <column name="value" index="0"/>
            <column name="name" index="1"/>
            <column name="path" index="2"/>
        </options>

    by this:
    
        <options from_data_table="blastdb" />
