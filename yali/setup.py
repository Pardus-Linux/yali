#!/usr/bin/env python
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

import os
import glob
import pyqtconfig
from distutils.core import setup, Extension
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.spawn import find_executable, spawn

YALI_VERSION = '0.1'


def qt_ui_files():
    p = "yali/gui/*.ui"
    return glob.glob(p)

def gui_pics():
    p = "yali/gui/pics"
    return glob.glob(p + "/*.png")

def help_files(lang):
    p = os.path.join("yali/gui/helps", lang)
    return glob.glob(p + "/*.html")


pyqt_configuration = pyqtconfig.Configuration()


def getRevision():
    import os
    try:
        p = os.popen("svn info 2> /dev/null")
        for line in p.readlines():
            line = line.strip()
            if line.startswith("Revision:"):
                return line.split(":")[1].strip()
    except:
        return ""

def getVersion():
    rev = getRevision()
    return "-r".join([YALI_VERSION, rev])    

def py_file_name(ui_file):
    return os.path.splitext(ui_file)[0] + '.py'


##
# build command
class YaliBuild(build):

    def compile_ui(self, ui_file):
        pyuic_exe = find_executable('pyuic', pyqt_configuration.default_bin_dir)
        if not pyuic_exe:
            # Search on the $Path.
            pyuic_exe = find_executable('pyuic')
    
        cmd = [pyuic_exe, ui_file, '-o']
        cmd.append(py_file_name(ui_file))
        spawn(cmd)

    def run(self):
        for f in qt_ui_files():
            self.compile_ui(f)

        build.run(self)

##
# clean command
class YaliClean(clean):

    def run(self):
        clean.run(self)

        # clean ui generated .py files
        for f in qt_ui_files():
            f = py_file_name(f)
            if os.path.exists(f):
                os.unlink(f)


mountmodule = Extension('mount',
                        sources = ['extensions/mount.c'],
                        extra_compile_args = ['-Wall'])


setup(name="yali",
      version= getVersion(),
      description="YALI (Yet Another Linux Installer)",
      long_description="Pardus System Installer.",
      license="GNU GPL2",
      author="Pardus Developers",
      author_email="yali@uludag.org.tr",
      url="http://www.uludag.org.tr/eng/yali/",
      packages = ['yali', 'yali.gui'],
      package_dir = {'': ''},
      data_files = [('/usr/share/yali/pics', gui_pics()),
                    ('/usr/share/yali/helps/en', help_files("en"))],
      scripts = ['yali-bin'],
      ext_modules = [mountmodule],
      cmdclass = {
        'build' : YaliBuild,
        'clean' : YaliClean
        }
    )
