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
import re
import glob
import shutil
import pyqtconfig
from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
from distutils.cmd import Command
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.install import install
from distutils.spawn import find_executable, spawn

import yali

YALI_VERSION = yali.__version__


def qt_ui_files():
    p = "yali/gui/*.ui"
    return glob.glob(p)

def gui_pics():
    p = "yali/gui/pics"
    return glob.glob(p + "/*.png")

def gui_slidepics():
    p = "yali/gui/slideshow/*.png"
    return glob.glob(p)

def user_faces():
    p = "yali/user_faces/*.png"
    return glob.glob(p)

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
#    rev = getRevision()
#    return "-r".join([YALI_VERSION, rev])
    # don't use svn revision...
    return YALI_VERSION
    

def py_file_name(ui_file):
    return os.path.splitext(ui_file)[0] + '.py'


##
# build command
class YaliBuild(build):

    def add_gettext_support(self, ui_file):
        # hacky, too hacky. but works...

        py_file = py_file_name(ui_file)
        # lines in reverse order
        lines =  ["_ = __trans.ugettext",
                 "__trans = gettext.translation('yali', fallback=True)\n",
                 "import gettext\n"]
        f = open(py_file, "r").readlines()
        for l in lines:
            f.insert(1, l)
        x = open(py_file, "w")
        for l in f:
            l = l.replace("self.__tr", "_")
            x.write(l)
        

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
            self.add_gettext_support(f)

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

##
# uninstall command
class YaliUninstall(Command):
    user_options = [ ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        yali_dir = os.path.join(get_python_lib(), "yali")
        if os.path.exists(yali_dir):
            print "removing: ", yali_dir
            shutil.rmtree(yali_dir)

        data_dir = "/usr/share/yali"
        if os.path.exists(data_dir):
            print "removing: ", data_dir
            shutil.rmtree(data_dir)



i18n_domain = "yali"
i18n_languages = "tr nl"

class I18nInstall(install):
    def run(self):
        install.run(self)
        for lang in i18n_languages.split(' '):
            print "Installing '%s' translations..." % lang
            os.popen("msgfmt po/%s.po -o po/%s.mo" % (lang, lang))
            if not self.root:
                self.root = "/"
            destpath = os.path.join(self.root, "usr/share/locale/%s/LC_MESSAGES" % lang)
            try:
                os.makedirs(destpath)
            except:
                pass
            shutil.copy("po/%s.mo" % lang, os.path.join(destpath, "%s.mo" % i18n_domain))



mountmodule = Extension('mount',
                        sources = ['extensions/mount.c'],
                        extra_compile_args = ['-Wall'])
rebootmodule = Extension('reboot',
                         sources = ['extensions/reboot.c'],
                         extra_compile_args = ['-Wall'])


setup(name="yali",
      version= getVersion(),
      description="YALI (Yet Another Linux Installer)",
      long_description="Pardus System Installer.",
      license="GNU GPL2",
      author="Pardus Developers",
      author_email="yali@uludag.org.tr",
      url="http://www.uludag.org.tr/eng/yali/",
      packages = ['yali', 'yali.asod', 'yali.gui'],
      package_dir = {'': ''},
      data_files = [('/usr/share/yali/pics', gui_pics()),
                    ('/usr/share/yali/slideshow', gui_slidepics()),
                    ('/usr/share/yali/user_faces', user_faces()),
                    ('/usr/share/yali/helps/en', help_files("en")),
                    ('/usr/share/yali/helps/tr', help_files("tr"))],
      scripts = ['yali-bin'],
      ext_modules = [mountmodule, rebootmodule],
      cmdclass = {
        'build' : YaliBuild,
        'clean' : YaliClean,
        'install': I18nInstall,
        'uninstall': YaliUninstall
        }
    )
