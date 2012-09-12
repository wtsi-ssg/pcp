#!/software/python-2.7.3/bin/python

import os
import ctypes
import time

clib=ctypes.CDLL("libc.so.6",use_errno=True)

class dirent(ctypes.Structure):
        _fields_ = [
            ("ino_t", ctypes.c_ulong),
            ("off_t", ctypes.c_ulong),
            ("d_reclen", ctypes.c_short),
            ("d_type",  ctypes.c_char ),
            ("d_name", ctypes.c_char * 4000)
        ]

class c_dir(ctypes.Structure):
    pass

dirent_p=ctypes.POINTER(dirent)
c_dir_p=ctypes.POINTER(c_dir)
opendir=clib.opendir
opendir.argtypes=[ctypes.c_char_p]
opendir.restype=c_dir_p
closedir=clib.closedir
closedir.argtypes=[c_dir_p]
closedir.restype=ctypes.c_int
readdir=clib.readdir
readdir.argtypes=[c_dir_p]
readdir.restype=dirent_p
            
def fastwalk(sourcedir):
    """
    yields (sourcedir,dirnames,filenames)
    """
    dirnames=[]
    filenames=[]
    
    dirp=opendir(sourcedir)
    if not bool(dirp):
        print "WARNING: Cannot open %s:"  %(sourcedir)
        print os.strerror(ctypes.get_errno())
        yield([],[],[])

    while True:
        p=readdir(dirp)
        if not p:
            break
        filename=p.contents.d_name
        filetype=p.contents.d_type

        if not filename in(".",".."):
            if filetype=="\x04":
                filetype="d"
                dirnames.append(filename)
            else:
                filetype="f"
		filenames.append(filename)
    closedir(dirp)
    yield sourcedir,dirnames,filenames

    for d in dirnames:
	fullpath=os.path.join(sourcedir,d)
        for i in fastwalk(fullpath):
            yield i
            



pathname="/lustre/scratch110/ensembl/th3"



for funcs in [os.walk, fastwalk]:

	totalfiles=0
	totaldirs=0
	starttime=time.time()
	print funcs,
	for path,files,dirs in funcs(pathname):
		totalfiles+=len(files)
		totaldirs+=len(dirs)
	endtime=time.time()
	print "%f seconds, %i dirs %i files" %(endtime-starttime,totalfiles,totaldirs)


