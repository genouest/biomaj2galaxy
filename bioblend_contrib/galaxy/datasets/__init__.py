"""
Contains possible interactions with the Galaxy Roles
"""
from bioblend.galaxy.client import Client
from bioblend.galaxy.datasets import DatasetClient
import urllib2

class DatasetClient(DatasetClient):

    def __init__(self, galaxy_instance):
        self.module = 'datasets'
        super(DatasetClient, self).__init__(galaxy_instance)

    def show_stderr(self, dataset_id, deleted=False):
        """
        Display stderr output of a dataset.
        """
        res = urllib2.urlopen(self.url[:-len("/api/datasets/")+1]+"/datasets/"+dataset_id+"/stderr")
        return res.read()
        
    def show_stdout(self, dataset_id, deleted=False):
        """
        Display stderr output of a dataset.
        """
        res = urllib2.urlopen(self.url[:-len("/api/datasets/")+1]+"/datasets/"+dataset_id+"/stdout")
        return res.read()
