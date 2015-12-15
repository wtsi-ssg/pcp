#Copyright Genome Research Ltd 2014
# Author gmpc@sanger.ac.uk
# This program is released under the GNU Public License V2 or later (GPLV2+)

import os
import errno

def safestat(filename):
    """lstat sometimes get Interrupted system calls; wrap it up so we can
    retry"""
    while True:
        try:
            statdata = os.lstat(filename)
            return(statdata)
        except IOError, error:
            if error.errno != errno.EINTR:
                raise
