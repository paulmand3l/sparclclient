import traceback

def genSparclException(response, verbose=False):
    """Given status from Server response.json(), which is a dict, generate
    a native SPARCL exception suitable for Science programs."""

    content = response.content
    if verbose:
        print(f'Exception: response content={content}')
    status = response.json()

    # As of Python 3.10.0.alpha6, python "match" statement could be used
    # instead of if-elif-else.
    # https://docs.python.org/3.10/whatsnew/3.10.html#pep-634-structural-pattern-matching
    if status.get('errorCode') == 'BADPATH':
        return BadPath(status.get('errorMessage'))
    else:
        return UnknownServerError(status.get('errorMessage'))


class BaseSparclException(Exception):
    """Base Class for all SPARCL exceptions. """
    error_code = 'UNKNOWN'
    error_message = '<NA>'
    traceback = None

    def get_subclass_name(self):
        return self.__class__.__name__

    def __init__(self, error_message, error_code=None):
        Exception.__init__(self)
        self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.traceback = traceback.format_exc()

    def __str__(self):
        return f'[{self.error_code}] {self.error_message}'

    def to_dict(self):
        """Convert a SPARCL exception to a python dictionary"""
        dd = dict(errorMessage = self.error_message,
                  errorCode = self.error_code)
        if settings.DEBUG and (self.traceback is not None):
            dd['traceback'] = self.traceback
        return dd

class BadPath(BaseSparclException):
    """A field path starts with a non-core field."""
    error_code = 'BADPATH'

class BadInclude(BaseSparclException):
    """Include list contains invalid data field(s)."""
    error_code = 'BADINCL'

class UnknownServerError(BaseSparclException):
    """Client got a status response from the SPARC Server that we do not
    know how to decode."""
    error_code = 'UNKNOWN'

class UnkDr(BaseSparclException):
    """The Data Release is not known or not supported."""
    error_code = 'UNKDR'

class ReadTimeout(BaseSparclException):
    """The server did not send any data in the allotted amount of time."""
    error_code = 'RTIMEOUT'


class UnknownSparcl(BaseSparclException):
    """Unknown SPARCL error.  If this is ever raised (seen in a log)
    create and use a new BaseSparcException exception that is more specific."""
    error_code = 'UNKSPARC'

# error_code values should be no bigger than 8 characters 12345678