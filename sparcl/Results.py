"""Containers for results from SPARCL Server.
These include results of client.retrieve() client.find().
"""

from collections import UserList
#!import copy
from sparcl.utils import _AttrDict


class Results(UserList):

    def __init__(self, dict_list, client=None):
        super().__init__(dict_list)
        self.hdr = dict_list[0]
        self.recs = dict_list[1:]
        self.client = client
        self.fields = client.fields
        self.to_science_fields()
        self.hdr['Count'] = len(self.recs)

    # https://docs.python.org/3/library/collections.html#collections.deque.clear
    def clear(self):
        super().clear()
        self.hdr = {}
        self.recs = []

    @property
    def info(self):
        return self.hdr

    @property
    def count(self):
        return self.hdr['Count']

    @property
    def records(self):
        return self.recs

    def json(self):
        return self.data

    def to_science_fields(self):  # from_orig
        """Convert Internal field names to Science field names.
        SIDE-EFFECT: modifies self.recs """
        newrecs = list()
        for rec in self.recs:
            newrec = dict()
            dr = rec['_dr']
            keep = True
            for orig in rec.keys():
                if orig == '_dr':
                    # keep DR around unchanged. We need it to rename back
                    # to Internal Field Names later.
                    newrec[orig] = rec[orig]
                else:
                    new = self.fields._science_name(orig, dr)
                    if new is None:
                        keep = False
                    newrec[new] = rec[orig]
            if keep:
                newrecs.append(_AttrDict(newrec))
        self.recs = newrecs

    def to_internal_fields(self):
        """Convert Science field names to Internal field names."""
        for rec in self.recs:
            dr = rec.get('_dr')
            for new in rec.keys():
                if new == '_dr':
                    # keep DR around unchanged. We need it to rename back
                    # to Internal Field Names later.
                    continue
                new = self.fields._internal_name(new, dr)
                rec[new] = rec.pop(new)


# For results of retrieve()
class Retrieved(Results):
    """Hold results of 'client.retrieve()"""

    def __init__(self, dict_list, client=None):
        super().__init__(dict_list, client=client)

    def __repr__(self):
        return f'Retrieved Results: {len(self.recs)} records'


class Found(Results):
    """@@@ NEEDS DOCUMENTATION !!!"""

    def __init__(self, dict_list, client=None):
        super().__init__(dict_list, client=client)

    def __repr__(self):
        return f'Find Results: {len(self.recs)} records'

    @property
    def ids(self):
        dr = list(self.fields.all_drs)[0]
        idfld = self.fields._science_name('id', dr)

        return [d.get(idfld) for d in self.recs]
