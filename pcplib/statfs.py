#Copyright Genome Research Ltd 2014
# Author gmpc@sanger.ac.uk
# This program is released under the GNU Public License V2 or later (GPLV2+)

import ctypes
"""
This module provides python bindings for statfs.
"""

# C data structures
class _fsid(ctypes.Structure):
    _fields_ = [
        ("val", ctypes.c_int * 2)
]

class _struct_statfs(ctypes.Structure):
    _fields_ = [
    ('f_type', ctypes.c_long),
    ('f_bsize', ctypes.c_long),
    ('f_blocks', ctypes.c_ulong),
    ('f_bfree', ctypes.c_ulong),
    ('f_bavail', ctypes.c_ulong),
    ('f_files', ctypes.c_ulong),
    ('f_ffree', ctypes.c_ulong),
    ('f_fsid', _fsid),
    ('f_namelen', ctypes.c_long),
    ('f_frsize', ctypes.c_long),
    ('f_flags', ctypes.c_long),
    ('f_spare', ctypes.c_long * 4)
]


_clib = ctypes.CDLL("libc.so.6", use_errno=True)
_struct_statfs_p = ctypes.POINTER(_struct_statfs)
_statfs = _clib.statfs
_statfs.argtypes = [ctypes.c_char_p, _struct_statfs_p]


def fstype(path):
    """Return the filesystem magic number for a  path. See the statfs"""

    data = _struct_statfs()
    _statfs(path, ctypes.byref(data))
    return hex(data.f_type)
