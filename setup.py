from distutils import sysconfig
from distutils.core import setup
from distutils.command.build import build

import subprocess
import ctypes.util
import os
import sys
import shutil
import re

VERSION_PY = """
# This file is originally generated from Git information by running 
#'setup.py  sdist'.  Distribution tarballs contain a pre-generated 
#copy of this file.

__version__ = '%s'
"""
def update_version():
    """Grab the version number out of git. If we are not in
    git, set if from _version.py which is generated as part
    of the source release process. (setup.py dsist).
    """

    ver = "UNKNOWN"
    if os.path.isdir(".git"):
        try:
            p = subprocess.Popen(["git", "describe",
                                  "--abbrev=4", "--tags",
                                  "--dirty"],
                                 stdout=subprocess.PIPE)
        except EnvironmentError:
            print "In a git repository, but unable to run git."

        stdout = p.communicate()[0]
        if p.returncode != 0:
            print "In a git repository, but unable to run git."

        ver = stdout.strip()
        f = open("_version.py", "w")
        f.write(VERSION_PY % ver)
        f.close()
        print "Setting version from git." 
    else:
        try:
            from _version import __version__ as ver
        except ImportError:
            ver = "UNKNOWN"
        print "Setting version from distribution."
    print "version '%s'" % ver
    return (ver)

def build_liblustre():
    """See if we have liblustreapi.so. If we do not have one,
    generate one from liblustreapi.a"""

    # See if we have a .so already installed in the system.
    liblocation = ctypes.util.find_library("lustreapi")
    if liblocation:
        print "Using system liblustreapi.so from %s" % liblocation
        return()
    # if we have a copy our lib directory, leave it alone.
    if os.path.exists("lib/liblustreapi.so"):
        print "Lustre library already built."
        return()

    have_sharedlib = False
    have_staticlib = False

    # Search user defined and system library locations until
    # we find one.
    lib_locations = ["/usr/lib","/lib"]
    if liblustre_loc:
        lib_locations.insert(0, liblustre_loc)

    for location in lib_locations:
        print "Looking for liblustreapi.[so|a] in %s" % location
        liblustre_shared = (os.path.join(location, "liblustreapi.so"))
        liblustre_static = (os.path.join(location, "liblustreapi.a"))

        if os.path.exists(liblustre_shared):
            have_sharedlib = True
            break
        if  os.path.exists(liblustre_static):
            have_staticlib = True
            break
    # Copy shared library into the dist tree.
    if have_sharedlib:
        print "Using liblustreapi.so from %s" %location
        shutil.copy(liblustre_shared,"lib/liblustreapi.so")
    # static lib needs converting to a .so
    if have_staticlib:
        print "Found liblustreapi.a in %s" % location
        convert_liblustre(location)

    if not ( have_staticlib or have_sharedlib ):
        print "ERROR: Unable to find liblustreapi."
        print_help()
        exit(1)
        
def print_help():
    print ""
    print ("This modules requires the liblustreapi C library.\n"
           "It should be installed as part of the lustre client package.\n" 
           "If the library is installed in a non standard location,\n"
		   "use the following option to setup.py to point to the\n"
		   "libary location:\n"
		   "\n"
		   "--with-liblustre=/path/to/library"
		   )
    print ""

def convert_liblustre(lib_location):
    """Convert liblustre.a to .so
    On linux amd64 we can do:
    ar -x liblustreapi.a ; gcc -shared *.o -o liblustreapi.so
    """ 
    
    liblustre=os.path.join(lib_location,"liblustreapi.a")
    print "Converting liblustreapi.a to liblustreapi.so"
    p = subprocess.Popen(["ar","-x","-v",liblustre],
                         stdout=subprocess.PIPE)
    stdout = p.communicate()[0]
    if p.returncode != 0:
        print "Error extracting liblustreapi.a"
        exit(1)

    p = subprocess.Popen(["gcc","-shared","liblustreapi.o",
                          "-o","lib/liblustreapi.so"],
                         stdout=subprocess.PIPE)
    stdout = p.communicate()[0]
    if p.returncode != 0:
        print "Error recompiling liblustreapi.so"
        exit(1)

    try:
        lustre = ctypes.CDLL("lib/liblustreapi.so")
        funptr = lustre.llapi_file_create

    except OSError, AttributeError:
        print "Unable to convert liblustreapi.a to a .so."
        print "Please read the README for hints on how to try"
        print "this yourself."
        exit(1)
    print "liblustreapi.a -> .so conversion sucessful."


class mybuild_py(build):
    def run(self):
        build_liblustre()
        build.run(self)
        

# Parse our optional argument
liblustre_loc = None
for arg in sys.argv:
    if "--with-liblustre=" in arg:
       	liblustre_loc = arg.split("=")[1]
       	sys.argv.remove(arg)

# Grab version out of git, or the dist tarball.
version = update_version()

# Check if the system supplies liblustreapi.so
# If not, we need to package our own.
liblocation = ctypes.util.find_library("lustreapi")
if liblocation:
    print "Using system liblustreapi.so from %s" % liblocation
    lustre_packagedata = {}
else:
    lustre_packagedata = {"lustre": ["liblustreapi.so"]}

setup(name = "pcp",
      cmdclass={"build": mybuild_py, 
                },
      description = "A parallel copy program",
      url = "https://github.com/wtsi-ssg/pcp",
      version = version,
      author = "Guy Coates",
      author_email = "gmpc@sanger.ac.uk",
      scripts = ["pcp"],
      packages=["lib"],
      package_data = lustre_packagedata,
)
