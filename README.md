=============
BioMAJ2Galaxy
=============

About
=====

With these python scripts you can perform the following actions on a Galaxy server:

    * Add new items to data libraries
    * Remove items from data libraries
    * Add new items to tool data tables using data managers
    * Remove items from data libraries

These scripts are primarily designed to be used as BioMAJ (http://biomaj.genouest.org) post processes,
but they can probably used directly from the command line if you need to.

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

The bioblend_contrib directory contains some code to extend the BioBlend library.

You need an API key to access your galaxy server. You need to use one from an admin account. The master API key defined in universe_wsgi.ini doesn't work at the time of writing this doc (2014-10-13).

allow_library_path_paste should be set in universe_wsgi.ini

There is a opened pull request concerning the removal of items from the data tables. You will need to apply the patch available here: https://bitbucket.org/galaxy/galaxy-central/pull-request/577/add-an-api-to-remove-items-from-tool-data/diff
Hopefully this patch will be merged in a stable galaxy version someday.

Usage
=====

To see how to use each script, just launch it with --help option.

Known problems
==============

    * There is currently no way to delete a folder contained inside a data library from the API. The workaround is to delete the whole data library, or individual datasets.
    * Twobit support is still incomplete
    * There is no way yet to remove from disk multi-volume blast databanks when using remove_galaxy_data_manager.py
    * Visualizations do not see the dbkeys
    
    
    * The blastdb and blastdb_p data tables are not currently used by the blast+ tools from the following repository: http://toolshed.g2.bx.psu.edu/view/devteam/ncbi_blast_plus (See https://github.com/peterjc/galaxy_blast/issues/22 for more info)
    Until the wrappers are updated, you can manually modify the file ncbi_blast_plus/tools/ncbi_blast_plus/ncbi_macros.xml and replace the blocks that look like this:
    
        <options from_file="blastdb.loc">
            <column name="value" index="0"/>
            <column name="name" index="1"/>
            <column name="path" index="2"/>
        </options>

    by this:
    
        <options from_data_table="blastdb" />
