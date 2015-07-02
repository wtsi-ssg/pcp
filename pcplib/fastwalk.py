# Copyright (c) Genome Research Ltd 2014
# Author Guy Coates <gmpc@sanger.ac.uk>
# This program is released under the GNU Public License V2 or later (GPLV2+)
import os
import readdir
import stat
import safestat

def fastwalk (sourcedir, onerror=None, topdown=True):
    """Improved version of os.walk: generates a tuple of (sourcedir,[dirs],
    [files]). This version tries to use readdir to avoid expensive stat
    operations on lustre."""
    
    dirlist = []
    filelist = []

    try:
        entries = readdir.readdir(sourcedir)
    except Exception as  err:
        if onerror is not None:
            onerror(err)
        return

    for entry in entries:
        name = entry.d_name
        filetype = entry.d_type
    
        if not name in (".", ".."):
            if filetype == readdir.dirent.DT_UNKNOWN:
                fullname = os.path.join(sourcedir, name)
                mode = safestat.safestat(fullname).st_mode
                if stat.S_ISDIR(mode):
                    filetype = readdir.dirent.DT_DIR
                else:
                    filetype = readdir.dirent.DT_REG

            if filetype == readdir.dirent.DT_DIR:
                dirlist.append(name)
            else:
                filelist.append(name)

    if topdown:
        yield sourcedir, dirlist, filelist

    for d in dirlist:
        fullname = os.path.join(sourcedir, d)
        for entries in fastwalk(fullname, onerror, topdown):
            yield entries

    if not topdown:
        yield sourcedir, dirlist, filelist
