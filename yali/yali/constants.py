# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

# YALI constants module defines a class with constant members. An
# object from this class can only bind values one to it's members.

import locale
from os.path import join

class _constant:
    "Constant members implementation"
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if self.__dict__.has_key(name):
            raise self.ConstError, "Can't rebind constant: %s" % name
        # Binding an attribute once to a const is available
        self.__dict__[name] = value

    def __delattr__(self, name):
        if self.__dict__.has_key(name):
            raise self.ConstError, "Can't unbind constant: %s" % name
        # we don't have an attribute by this name
        raise NameError, name

class Constants:

    __c = _constant()

    def __init__(self):

        self.__c.pardus_version = "Pardus 1.0 RC"

        self.__c.log_file = "/tmp/install.log"

        # directories
        self.__c.data_dir = "/usr/share/yali"

        self.__c.mnt_dir = "/mnt"
        # new system will be installed directly into this target directory
        self.__c.target_dir = join(self.__c.mnt_dir, "target")
        # packages (and maybe others) will be in this source (cdrom) directory
        self.__c.source_dir = join(self.__c.mnt_dir, "cdrom")

        # swap file path
        self.__c.swap_file_name = ".swap"
        self.__c.swap_file_path = join(self.__c.target_dir, 
                                       self.__c.swap_file_name)

        # user faces
        self.__c.user_faces_dir = join(self.__c.data_dir, "user_faces")


        # pisi repository
        self.__c.repo_name = "pardus-devel-cd"
        self.__c.repo_uri = join(self.__c.source_dir, "repo/pisi-index.xml")

        # before release
        # pardus-devel repository
        self.__c.devel_repo_name = "pardus-devel"
        self.__c.devel_repo_uri = "http://paketler.uludag.org.tr/pardus-devel/pisi-index.xml"


        # min root partition size
        self.__c.min_root_size = 3500

    def __getattr__(self, attr):
        return getattr(self.__c, attr)

    def __setattr__(self, attr, value):
        setattr(self.__c, attr, value)

    def __delattr__(self, attr):
        delattr(self.__c, attr)


consts = Constants()
try:
    consts.lang = locale.getlocale()[0][:2]
except:
    # default lang to en_US
    consts.lang = "en"
