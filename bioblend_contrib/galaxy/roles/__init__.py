"""
Contains possible interactions with the Galaxy Roles
"""
from bioblend.galaxy.client import Client


class RolesClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'roles'
        super(RolesClient, self).__init__(galaxy_instance)

    def get_roles(self):
        """
        Displays a collection (list) of roles.


        :rtype: list
        :return: A list of dicts with details on individual roles.
                 For example::

                   [ {"roles_url": "/api/groups/33abac023ff186c2/roles",
                   "name": "Listeria", "url": "/api/groups/33abac023ff186c2",
                   "users_url": "/api/groups/33abac023ff186c2/users",
                   "model_class": "Group", "id": "33abac023ff186c2"},
                   {"roles_url": "/api/groups/73187219cd372cf8/roles",
                   "name": "LPN", "url": "/api/groups/73187219cd372cf8",
                   "users_url": "/api/groups/73187219cd372cf8/users",
                   "model_class": "Group", "id": "73187219cd372cf8"}
                   ]


        """
        return Client._get(self)

    def show_role(self, role_id):
        """
        Display information on a single role

        :type role_id: string
        :param role_id: Encoded role ID


        :rtype: dict
        :return: A description of role
                 For example::

                   {"roles_url": "/api/groups/33abac023ff186c2/roles",
                   "name": "Listeria", "url": "/api/groups/33abac023ff186c2",
                   "users_url": "/api/groups/33abac023ff186c2/users",
                   "model_class": "Group", "id": "33abac023ff186c2"}

        """

        return Client._get(self, id=role_id)
