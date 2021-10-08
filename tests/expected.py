boss_record_structure = {
    'and_mask': '<list(4589)[0]>:int',
    'aux.FIBERID': 'int',
    'aux.MJD': 'int',
    'aux.PLATEID': 'int',
    'aux.RUN2D': 'str',
    'data_release': 'str',
    'dec_center': 'float',
    'dirpath': 'str',
    'filename': 'str',
    'filesize': 'int',
    'flux': '<list(4589)[0]>:float',
    'ivar': '<list(4589)[0]>:float',
    'loglam': '<list(4589)[0]>:float',
    'model': '<list(4589)[0]>:float',
    'ra_center': 'float',
    'redshift': 'float',
    'sky': '<list(4589)[0]>:float',
    'specid': 'int',
    'spectra.coadd.OR_MASK': '<list(4589)[0]>:int',
    'wdisp': '<list(4589)[0]>:float'}

boss_numpy = [
    'aux.FIBERID',
    'aux.MJD',
    'aux.PLATEID',
    'aux.RUN2D',
    'coadd',
    'data_release',
    'dec_center',
    'dirpath',
    'filename',
    'filesize',
    'ra_center',
    'redshift',
    'specid']

boss_pandas = [
    'aux.FIBERID',
    'aux.MJD',
    'aux.PLATEID',
    'aux.RUN2D',
    'data_release',
    'dec_center',
    'df',
    'dirpath',
    'filename',
    'filesize',
    'ra_center',
    'redshift',
    'specid']

boss_spectrum1d = [
    'and_mask',
    'aux.FIBERID',
    'aux.MJD',
    'aux.PLATEID',
    'aux.RUN2D',
    'data_release',
    'dec_center',
    'dirpath',
    'filename',
    'filesize',
    'model',
    'ra_center',
    'redshift',
    'sky',
    'spec1d',
    'specid',
    'spectra.coadd.OR_MASK',
    'wdisp']