# Copyright (c) Genome Research Ltd 2012
# Author Guy Coates <gmpc@sanger.ac.uk>
# This program is released under the GNU Public License V2 (GPLv2)

"""
Python bindings to minimal subset of lustre api.
This module requires a dynamically linked version of the lustre
client library (liblustreapi.so). 

Older version of the lustre client only ships a static library (liblustreapi.a).
setup.py should have generated a dynamic version during installation.

You can generate the dynamic library by hand by doing the following:

ar -x liblustreapi.a
gcc -shared -o liblustreapi.so *.o

"""
import ctypes
import ctypes.util
import os
import select
import sys


import pkg_resources
try:
    __version__ = pkg_resources.require("pcp")[0].version
except pkg_resources.DistributionNotFound:
    __version__ = "UNRELEASED"

LUSTREMAGIC = 0xbd00bd0

liblocation = ctypes.util.find_library("lustreapi")
# See if liblustreapi.so is in the same directory as the module
if not liblocation:
    modlocation, module = os.path.split(__file__)
    liblocation = os.path.join(modlocation, "liblustreapi.so")

lustre = ctypes.CDLL(liblocation, use_errno=True)

# ctype boilerplate for C data structures and functions
class lov_user_ost_data_v1(ctypes.Structure):
    _fields_ = [
        ("l_object_id", ctypes.c_ulonglong),
        ("l_object_gr", ctypes.c_ulonglong),
        ("l_ost_gen", ctypes.c_uint),
        ("l_ost_idx", ctypes.c_uint)
        ]
class lov_user_md_v1(ctypes.Structure):
    _fields_ = [
        ("lmm_magic", ctypes.c_uint),
        ("lmm_pattern", ctypes.c_uint),
        ("lmm_object_id", ctypes.c_ulonglong),
        ("lmm_object_gr", ctypes.c_ulonglong),
        ("lmm_stripe_size", ctypes.c_uint),
        ("lmm_stripe_count",  ctypes.c_short),
        ("lmm_stripe_offset", ctypes.c_short),
        ("lmm_objects", lov_user_ost_data_v1 * 2000 ),
        ]
lov_user_md_v1_p = ctypes.POINTER(lov_user_md_v1)
lustre.llapi_file_get_stripe.argtypes = [ctypes.c_char_p, lov_user_md_v1_p]
lustre.llapi_file_open.argtypes = [ctypes.c_char_p, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_ulong, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int]
lustre.llapi_lov_get_uuids.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]

class stripeObj:
    """
    lustre stripe object.

    This object contains details of the striping of a lustre file.

    Attributes:
      lovdata:  lov_user_md_v1 structure as returned by the lustre C API.
      stripecount: Stripe count.
      stripesize:  Stripe size (bytes).
      stripeoffset: Stripe offset.
      ostobjects[]: List of lov_user_ost_data_v1 structures as returned by the
      C API.
    """
    def __init__(self):
        self.lovdata = lov_user_md_v1()
        self.stripecount = -1
        self.stripesize = 0
        self.stripeoffset = -1
        self.ostobjects = []

    def __str__(self):
        string = "Stripe Count: %i Stripe Size: %i Stripe Offset: %i\n" \
                 % (self.stripecount, self.stripesize, self.stripeoffset)
        for ost in self.ostobjects:
            string += ("Objidx:\t %i \tObjid:\t %i\n" % (ost.l_ost_idx,
                                                         ost.l_object_id))
        return(string)

    def isstriped(self):
        if self.stripecount > 1 or self.stripecount == -1:
            return(True)
        else:
            return(False)

def ostcount(filename):
    """Returns number of OSTs on the filesystem hosting a file or directory.

    Arguments:
        filename: The name of a file or directory to query.

    Returns:
        An integer.

    """
    fd = os.open(filename,os.O_RDONLY)
    count = ctypes.c_int()
    try:
        err = lustre.llapi_lov_get_uuids(fd, None, ctypes.byref(count))
        if err != 0:
            raise IOError(err, os.strerror(err))
        return count.value
    finally:
        os.close(fd)

def getstripe(filename):
    """Returns a stripeObj containing the stipe information of filename.

    Arguments:
      filename: The name of the file to query.

    Returns:
      A stripeObj containing the stripe information.
    
    """
    stripeobj = stripeObj()
    lovdata = lov_user_md_v1()
    stripeobj.lovdata = lovdata
    err = lustre.llapi_file_get_stripe(filename, ctypes.byref(lovdata))

    # err 61 is due to  LU-541 (see below)
    if err < 0 and err != -61:
        err = 0 - err
        raise IOError(err, os.strerror(err))

    # workaround for Whamcloud LU-541
    # use the filesystem defaults if no properties set
    if err == -61  :
        stripeobj.stripecount = 0
        stripeobj.stripesize = 0
        stripeobj.stripeoffset = -1

    else:
        for i in range(0, lovdata.lmm_stripe_count):
            stripeobj.ostobjects.append(lovdata.lmm_objects[i])

        stripeobj.stripecount = lovdata.lmm_stripe_count
        stripeobj.stripesize = lovdata.lmm_stripe_size
        # lmm_stripe_offset seems to be reported as 0, which is wrong
        if len(stripeobj.ostobjects) > 0:
            stripeobj.stripeoffset = stripeobj.ostobjects[0].l_ost_idx
        else:
            stripeobj.stripeoffset = -1
    return(stripeobj)

def setstripe(filename, stripeobj=None, stripesize=0, stripeoffset=-1,
              stripecount=1):
    """Sets the striping on an existing directory, or create a new empty file
    with the specified striping. Stripe parameters can be set explicity, or
    you can pass in an existing stripeobj to copy the attributes from an
    existing file.

    Note you can set the striping on an existing directory, but you cannot set
    the striping on an existing file.
    
    Arguments:
      stripeobj: copy the parameters from stripeobj.
      stripesize: size of stripe in bytes
      stripeoffset: stripe offset
      stripecount: stripe count

    Examples:
      #Set the filesystem defaults
      setstripe("/lustre/testfile")

      # Stripe across all OSTs.
      setstripe("/lustre/testfile", stripecount=-1)

      #copy the attributes from foo
      stripeobj = getstripe("/lustre/foo")
      setstripe("/lustre/testfile", stripeobj)

    """
    flags = os.O_CREAT
    mode = 0700
    # only stripe_pattern 0 is supported by lustre.
    stripe_pattern = 0

    if stripeobj:
        stripesize = stripeobj.stripesize
        stripeoffset = stripeobj.stripeoffset
        stripecount = stripeobj.stripecount


    # Capture the lustre error messages, These get printed to stderr via 
    # liblusteapi, and so we need to intercept them.

    message = captureStderr()

    fd = lustre.llapi_file_open(filename, flags, mode, stripesize,
                                stripeoffset, stripecount, stripe_pattern)
    message.readData()
    message.stopCapture()

    if fd < 0:
        err = 0 - fd
        raise IOError(err, os.strerror(err))
    else:
        os.close(fd)
        return(0)


class captureStderr():
    """This class intercepts stderr and stores any output"""
    def __init__(self):
        self.pipeout, self.pipein = os.pipe()
        self.oldstderr = os.dup(2)
        os.dup2(self.pipein, 2)
        self.contents=""

    def __str__(self):
        return (self.contents)

    def readData(self):
        """Read data from stderr until there is no more."""
        while self.checkData():
            self.contents += os.read(self.pipeout, 1024)
            
    def checkData(self):
        """Check to see if there is any data to be read."""
        r, _, _ = select.select([self.pipeout], [], [], 0)
        return bool(r)

    def stopCapture(self):
        """Restore the original stderr"""
        os.dup2(self.oldstderr, 2)
        os.close(self.pipeout)
        os.close(self.pipein)
