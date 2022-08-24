"""Client module for SPARCL.
This module interfaces to the SPARC-Server to get spectra data.
"""
# python -m unittest tests.tests_api
############################################
# Python Standard Library
from urllib.parse import urlencode, urlparse
from warnings import warn
import pickle
#!from pathlib import Path
import tempfile
############################################
# External Packages
import requests
############################################
# Local Packages
from sparcl.fields import Fields
import sparcl.utils as ut
import sparcl.exceptions as ex
#!import sparcl.type_conversion as tc
from sparcl import __version__
from sparcl.Results import Found, Retrieved


pat_hosts = ['sparc1.datalab.noirlab.edu',
             'sparc2.datalab.noirlab.edu',
             'astrosparcl.datalab.noirlab.edu']

# Upload to PyPi:
#   python3 -m build --wheel
#   twine upload dist/*

# Use Google Style Python Docstrings so autogen of Sphinx doc works:
#  https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html#example-google
#
# Use sphinx-doc emacs minor mode to insert docstring skeleton.
# C-c M-d in function/method def

# ### Generate documentation:
# cd ~/sandbox/sparclclient
# sphinx-apidoc -f -o source sparcl
# make html
# firefox -new-tab "`pwd`/build/html/index.html"

# Using HTTPie (http://httpie.org):
# http :8030/sparc/version

# specids = [394069118933821440, 1355741587413428224, 1355617892355303424,
#   1355615143576233984, 1355661872820414464, 1355755331308775424,
#   1355716848401803264]
# client = api.api.SparclClient(url='http://localhost:8030/sparc')
# client.retrieve(specids)[0].keys() # >> dict_keys(['flux','loglam'])
#
# data0 = client.retrieve(specids,columns='flux')
# f'{len(str(data0)):,}'   # -> '3,435,687'
#
# dataall = client.retrieve(specids,columns=allc)
# f'{len(str(dataall)):,}' # -> '27,470,052'

_PROD  = 'https://astrosparcl.datalab.noirlab.edu'  # noqa: E221
_STAGE = 'https://sparclstage.datalab.noirlab.edu'  # noqa: E221
_PAT   = 'https://sparc1.datalab.noirlab.edu'       # noqa: E221
_DEV   = 'http://localhost:8050'                    # noqa: E221


#client_version = pkg_resources.require("sparclclient")[0].version
client_version = __version__

DEFAULT = 'DEFAULT'
ALL = 'ALL'
RESERVED = set([DEFAULT, ALL])


###########################
# ## Convenience Functions

# Following can be done with:
#   set.intersection(*sets)
#
#!def intersection(*lists):
#!    """Return intersection of all LISTS."""
#!    return set(lists[0]).intersection(*lists[1:])

def records_field_list(records):
    """Get list of fields used in records. One list per Data Set.
    Args:
        records (list): List of records (each is a dictionary).
    Returns:
        dict: dict[Data_Set] = [field_name1, ...]
    :param records: List of records (each is a dictionary)
    :returns: dict[Data_Set] = [field_name1, ...]
    Example:
      >>> from api.client import fields_available
      >>> recs = client.sample_records(3)
      >>> flds = fields_available(recs)
    Example:
        >>> from sparcl.client import fields_available
        >>> recs = client.sample_records(3)
        >>> flds = fields_available(recs)
    """
    fields = {r._dr: sorted(r.keys()) for r in records}
    return fields


###########################
# ## The Client class

class SparclClient():  # was SparclApi()
    """Provides interface to SPARCL Server.
    When using this to report a bug, set verbose to True. Also print
    your instance of this.  The results will include important info
    about the Client and Server that is usefule to Developers.
    :param url: Base URL of SPARC Server
    :param verbose: (True,[False]) Default verbosity for all client methods.
    :param verbose: (True,[False]) True:: override field renaming
    :param connect_timeout [1.1]: Number of seconds to wait to establish
               connection with server.
    :param read_timeout [5400]: Number of seconds to wait for server to send
               a response. (generally time to wait for first byte)
    Args:
        url (str): Base URL of SPARC Server.

        verbose (:obj:`bool`, optional): Default verbosity is set to
        False for all client methods.

        connect_timeout (:obj:`float`, optional): Number of seconds to
            wait to establish connection with server.  Defaults to
            1.1.

        read_timeout (:obj:`float`, optional): Number of seconds to
            wait for server to send a response.  Generally time to
            wait for first byte. Defaults to 5400.

    Example:
        >>> client = SparclClient(verbose=True)
        >>> print(client)

    Raises:
        Exception: Object creation compares the version from the
            Server against the one expected by the Client. Throws an
            error if the Client is a major version or more behind.

    """

    KNOWN_GOOD_API_VERSION = 8.0  # @@@ Change this on Server version increment

    def __init__(self, *,
                 url=_PROD,
                 verbose=False,
                 connect_timeout=1.1,    # seconds
                 read_timeout=90 * 60):  # seconds
        """Create client instance.
        """
        self.rooturl = url.rstrip("/")
        self.apiurl = f'{self.rooturl}/sparc'
        self.apiversion = None
        self.verbose = verbose
        #!self.internal_names = internal_names
        self.c_timeout = float(connect_timeout)  # seconds
        self.r_timeout = float(read_timeout)     # seconds

        # require response within this num seconds
        # https://2.python-requests.org/en/master/user/advanced/#timeouts
        # (connect timeout, read timeout) in seconds
        self.timeout = (self.c_timeout, self.r_timeout)
        #@@@ read timeout should be a function of the POST payload size

        if verbose:
            print(f'apiurl={self.apiurl}')

        # Get API Version
        try:
            endpoint = f'{self.apiurl}/version/'
            verstr = requests.get(endpoint, timeout=self.timeout).content
        except requests.ConnectionError as err:
            msg = f'Could not connect to {endpoint}. {str(err)}'
            if urlparse(url).hostname in pat_hosts:
                msg += 'Did you enable VPN?'
            raise ex.ServerConnectionError(msg) from None  # disable chaining

        self.apiversion = float(verstr)

        expected_api = SparclClient.KNOWN_GOOD_API_VERSION
        if (int(self.apiversion) - int(expected_api)) >= 1:
            msg = (f'The SPARCL Client you are running expects an older '
                   f'version of the API services. '
                   f'Please upgrade to the latest "sparclclient".  '
                   f'The Client you are using expected version '
                   f'{SparclClient.KNOWN_GOOD_API_VERSION} but got '
                   f'{self.apiversion} from the SPARCL Server '
                   f'at {self.apiurl}.')
            raise Exception(msg)
        #self.session = requests.Session() #@@@

        self.clientversion = client_version
        self.fields = Fields(self.apiurl)

        ###
        ####################################################
        # END __init__()

    def __repr__(self):
        #!f' internal_names={self.internal_names},'
        return(f'(sparclclient:{self.clientversion},'
               f' api:{self.apiversion},'
               f' {self.apiurl},'
               f' verbose={self.verbose},'
               f' connect_timeout={self.c_timeout},'
               f' read_timeout={self.r_timeout})')

    @property
    def all_datasets(self):
        return self.fields.all_drs

    def get_default_fields(self, *, dataset_list=None):
        """Get fields tagged as 'default' that are in DATASET_LIST.
        This is the fields used for the DEFAULT value of the include parameter
        of client.retrieve().

        If DATASET_LIST is None (the default),
        get the /intersection/ of 'default' fields across all DATASET_LIST."""

        if dataset_list is None:
            dataset_list = self.fields.all_drs

        assert isinstance(dataset_list, (list, set)), (
            f'DATASET_LIST must be a list. Found {dataset_list}')

        common = set(self.fields.common(dataset_list))
        union = self.fields.default_retrieve_fields(dataset_list=dataset_list)
        return sorted(common.intersection(union))

    def get_all_fields(self, *, dataset_list=None):
        """Get fields tagged as 'all' that are in DATA_SET.
        This is the fields used for the ALL value of the include parameter
        of client.retrieve().

        If DATA_SET is None (the default),
        get the /intersection/ of 'all' fields across all DATASET_LIST."""
        common = set(self.fields.common(dataset_list))
        union = self.fields.all_retrieve_fields(dataset_list=dataset_list)
        return sorted(common.intersection(union))

    def _validate_science_fields(self, science_fields, *, dataset_list=None):
        """Raise exception if any field name in SCIENCE_FIELDS is
        not registered in at least one of DATASET_LIST."""
        if dataset_list is None:
            dataset_list = self.fields.all_drs
        all = set(self.fields.common(dataset_list=dataset_list))
        unk = set(science_fields) - all
        if len(unk) > 0:
            drs = self.fields.all_drs if dataset_list is None else dataset_list
            msg = (f'Unknown fields \"{",".join(unk)}\" given '
                   f'for DataSets {",".join(drs)}. '
                   f'Allowed fields are: {",".join(all)}. ')
            raise ex.UnknownField(msg)
        return True

    def _common_internal(self, *, science_fields=None, dataset_list=None):
        self._validate_science_fields(science_fields,
                                      dataset_list=dataset_list)

        if dataset_list is None:
            dataset_list = self.fields.all_drs
        if science_fields is None:
            science_fields = self.fields.all_fields
        common = self.fields.common_internal(dataset_list)
        flds = set()
        for dr in dataset_list:
            for sn in science_fields:
                flds.add(self.fields._internal_name(sn, dr))
        return common.intersection(flds)

    # Return Science Field Names (not Internal)
    def get_available_fields(self, *, dataset_list=None):
        """Get subset of fields that are in all (or selected) DATASET_LIST.
        This may be a bigger list than will be used with the ALL keyword to
        client.retreive()

        dataset_list :: list, None=All_Available
        """
        drs = self.fields.all_drs if dataset_list is None else dataset_list
        every = [set(self.fields.n2o[dr]) for dr in drs]
        return set.intersection(*every)

    @property
    def version(self):
        """Return version of Server Rest API used by this client.
        If the Rest API changes such that the Major version increases,
        a new version of this module will likely need to be used.
        Returns:
            float: API version.
        Example:
            >>> SparclClient('http://localhost:8030').version
            1.0
        """
        if self.apiversion is None:
            response = requests.get(f'{self.apiurl}/version',
                                    timeout=self.timeout,
                                    cache=True)
            self.apiversion = float(response.content)
        return self.apiversion

    def find(self, outfields=None, *,
             constraints={},  # dict(fname) = [op, param, ...]
             dataset_list=None,
             limit=500,
             sort=None):
        """sort :: comma seperated list of fields to sort by"""
        # Let "outfields" default to ['id']; but fld may have been renamed
        if outfields is None:
            dslist = list(self.fields.all_datasets)
            idfld = self.fields._science_name('id', dslist[0])
            if idfld not in self.fields.common():
                msg = (f'The "id" field ("{idfld}" is not common to all '
                       f'current Data Sets ({(", ").join(dslist)}) '
                       f'so we cannot use the default outfields="{idfld}".'
                       )
                raise ex.NoCommonIdField(msg)
            outfields = [idfld]
        if dataset_list is None:
            dataset_list = self.fields.all_drs
        self._validate_science_fields(outfields, dataset_list=dataset_list)
        dr = list(dataset_list)[0]
        if len(constraints) > 0:
            self._validate_science_fields(constraints.keys(),
                                          dataset_list=dataset_list)
            constraints = {self.fields._internal_name(k, dr): v
                           for k, v in constraints.items()}
        uparams = dict(limit=limit,)
        if sort is not None:
            uparams['sort'] = sort
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/find/?{qstr}'
        outfields = [self.fields._internal_name(s, dr) for s in outfields]
        search = [[k] + v for k, v in constraints.items()]
        sspec = dict(outfields=outfields, search=search)
        #!print(f'DBG find: outfields={outfields} search={search}')
        res = requests.post(url, json=sspec, timeout=self.timeout)

        if res.status_code != 200:
            #!print(f'DBG: res.content={res.content}') #@@@
            if self.verbose and ('traceback' in res.json()):
                #!print(f'DBG: res.json={res.json()}')
                print(f'DBG: Server traceback=\n{res.json()["traceback"]}')
            raise ex.genSparclException(res, verbose=self.verbose)

        return Found(res.json(), client=self)

    def missing(self, uuid_list, *, dataset_list=None,
                countOnly=False, verbose=False):
        """Return the subset of the given uuid_list that is NOT stored
        in the database.
        Args:
           uuid_list (list): List of uuids.
           countOnly (:obj:`bool`, optional): Set to True to return only
               a count of the missing uuids from the list. Defaults to False.
           verbose (:obj:`bool`, optional): Set to True for in-depth return
               statement.
               Defaults to False.
        Returns:
            list: The subset of the given uuid_list that is NOT stored in the
                database.
        Example:
            >>> si = ['0b1128aa-609e-48f7-ace6-f87a4e2c09ec']
            >>> client.missing_uuids(si)
            ['0b1128aa-609e-48f7-ace6-f87a4e2c09ec']
        """
        if dataset_list is None:
            dataset_list = self.fields.all_drs
        assert isinstance(dataset_list, (list, set)), (
            f'DATASET_LIST must be a list. Found {dataset_list}')

        verbose = verbose or self.verbose
        uparams = dict(dataset_list=','.join(dataset_list))
        qstr = urlencode(uparams)
        url = f'{self.apiurl}/missing/?{qstr}'
        uuids = list(uuid_list)
        if verbose:
            print(f'Using url="{url}"')
        res = requests.post(url, json=uuids, timeout=self.timeout)

        res.raise_for_status()
        if res.status_code != 200:
            raise Exception(res)
        ret = res.json()
        return ret
        # END missing_uuids()

    # Include fields are Science (not internal) names. But the mapping
    # of Internal to Science name depends on DataSet.  Its possible
    # for a field (Science name) to be valid in one DataSet but not
    # another.  For the include_list to be valid, all fields must be
    # valid Science field names for all DS in given dataset_list.
    # (defaults to all DataSets ingested)
    def _validate_include(self, include_list, dataset_list):
        if not isinstance(include_list, (list, set)):
            msg = f'Bad INCLUDE_LIST. Must be list. Got {include_list}'
            raise ex.BadInclude(msg)

        available_science = self.get_available_fields(
            dataset_list=dataset_list)
        inc_set = set(include_list)
        unknown = inc_set.difference(available_science)
        if len(unknown) > 0:
            msg = (f'The INCLUDE list ({",".join(sorted(include_list))}) '
                   f'contains invalid data field names '
                   f'for Data Sets ({",".join(sorted(dataset_list))}). '
                   f'Unknown fields are: '
                   f'{", ".join(sorted(list(unknown)))}. '
                   f'Available fields are: '
                   f'{", ".join(sorted(available_science))}.')
            raise ex.BadInclude(msg)
        return True

    def retrieve(self,  # noqa: C901
                 uuid_list,
                 *,
                 svc='spectras',  # 'retrieve',
                 format='pkl',    # 'json',
                 include='DEFAULT',
                 dataset_list=None,
                 limit=500,
                 chunk=500,
                 verbose=None):
        """Get spectrum by UUID (universally unique identifier) list.
        Args:
           uuid_list (list): List of uuids.

           dataset_list:: list, None  @@@

           include (list, 'DEFAULT', 'ALL'): List of field names to
              include in each record. (default: 'DEFAULT') verbose
              (boolean, optional): (default: False)
              SPECIAL CASES: field not in ALL DS @@@

        Returns:
           List of records. Each record is a dictionary of named fields.

        Example:
           >>> ids = ['c3fd34b2-3d47-4bb5-8cd6-e7d1787b81d3',]
           >>> res = client.retrieve(ids, include=['flux'])

        """
        if dataset_list is None:
            dataset_list = self.fields.all_drs
        assert isinstance(dataset_list, (list, set)), (
            f'DATASET_LIST must be a list. Found {dataset_list}')

        verbose = self.verbose if verbose is None else verbose

        if (include == DEFAULT) or (include is None) or include == []:
            include_list = self.get_default_fields(dataset_list=dataset_list)
        elif include == ALL:
            include_list = self.get_all_fields(dataset_list=dataset_list)
        else:
            include_list = include
        #! print(f'dbg0: include={include} include_list={include_list} '
        #!       f'dataset_list={dataset_list}')

        self._validate_include(include_list, dataset_list)

        com_include = self._common_internal(
            science_fields=include_list,
            dataset_list=dataset_list)
        uparams = dict(include=','.join(com_include),
                       limit=limit,
                       chunk_len=chunk,
                       format=format,
                       dataset_list=','.join(dataset_list))
        qstr = urlencode(uparams)

        #!url = f'{self.apiurl}/retrieve/?{qstr}'
        url = f'{self.apiurl}/{svc}/?{qstr}'
        if verbose:
            print(f'Using url="{url}"')
            ut.tic()

        try:
            ids = list(uuid_list)
            res = requests.post(url, json=ids, timeout=self.timeout)
        except requests.exceptions.ConnectTimeout as reCT:
            raise ex.UnknownSparcl(f'ConnectTimeout: {reCT}')
        except requests.exceptions.ReadTimeout as reRT:
            msg = (f'Try increasing the value of the "read_timeout" parameter'
                   f' to "SparclClient()".'
                   f' The current values is: {self.r_timeout} (seconds)'
                   f'{reRT}')
            raise ex.ReadTimeout(msg) from None
        except requests.exceptions.ConnectionError as reCE:
            raise ex.UnknownSparcl(f'ConnectionError: {reCE}')
        except requests.exceptions.TooManyRedirects as reTMR:
            raise ex.UnknownSparcl(f'TooManyRedirects: {reTMR}')
        except requests.exceptions.HTTPError as reHTTP:
            raise ex.UnknownSparcl(f'HTTPError: {reHTTP}')
        except requests.exceptions.URLRequired as reUR:
            raise ex.UnknownSparcl(f'URLRequired: {reUR}')
        except requests.exceptions.RequestException as reRE:
            raise ex.UnknownSparcl(f'RequestException: {reRE}')
        except Exception as err:  # fall through
            raise ex.UnknownSparcl(err)

        #!print(f'DBG: retrieve-3 res={res} len(content)={len(res.content)}')
        if verbose:
            elapsed = ut.toc()
            print(f'Got response to post in {elapsed} seconds')
        if res.status_code != 200:
            #!print(f'DBG: res.content={res.content}') #@@@
            if verbose and ('traceback' in res.json()):
                #!print(f'DBG: res.json={res.json()}')
                print(f'DBG: Server traceback=\n{res.json()["traceback"]}')
            #!raise ex.genSparclException(**res.json())
            raise ex.genSparclException(res, verbose=verbose)

        #!meta,*records = res.json()
        if format == 'json':
            results = res.json()
        elif format == 'pkl':
            # Read chunked binary file (representing pickle file) from
            # server response. Load pickle into python data structure.
            # Python structure is list of records where first element
            # is a header.
            with tempfile.TemporaryFile(mode='w+b') as fp:
                for idx, chunk in enumerate(res.iter_content(chunk_size=None)):
                    fp.write(chunk)
                # Position to start of file for pickle reading (load)
                fp.seek(0)
                results = pickle.load(fp)
        else:
            results = res.json()

        meta = results[0]
        if verbose:
            count = len(results) - 1
            print(f'Got {count} spectra in '
                  f'{elapsed:.2f} seconds ({count/elapsed:.0f} '
                  'spectra/sec)')
            print(f'{meta["status"]}')

        if len(meta['status'].get('warnings', [])) > 0:
            warn(f"{'; '.join(meta['status'].get('warnings'))}",
                 stacklevel=2)

        #! return Results( # @@@ Removed type conversion!!!
        #!     [ut._AttrDict(tc.convert(r, rtype, self, include))
        #!      for r in records],
        #!     client=self)
        #!return Retrieved([ut._AttrDict(r) for r in records],  client=self)
        #!print(f'dbg9: len(results)={len(results)}')
        return Retrieved(results, client=self)

    def retrieve_by_specid(self,
                           specid_list,
                           *,
                           include='DEFAULT',
                           dataset_list=None,
                           verbose=False):
        if dataset_list is None:
            constraints = {'specid': specid_list}
        else:
            constraints = {'specid': specid_list,
                           'data_release': dataset_list}

        # Science Field Name for uuid.
        dr = list(self.fields.all_drs)[0]
        idfld = self.fields._science_name('id', dr)

        found = self.find([idfld], constraints=constraints)
        if verbose:
            print(f'Found {found.count} matches.')
        res = self.retrieve(found.ids,
                            include=include,
                            dataset_list=dataset_list,
                            verbose=verbose)
        if verbose:
            print(f'Got {res.count} records.')
        return res


if __name__ == "__main__":
    import doctest
    doctest.testmod()
