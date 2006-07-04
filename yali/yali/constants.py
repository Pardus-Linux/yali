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

    def __getattr__(self, attr):
        return getattr(self.__c, attr)

    def __setattr__(self, attr, value):
        setattr(self.__c, attr, value)

    def __delattr__(self, attr):
        delattr(self.__c, attr)



consts = Constants()

consts.pardus_version = "Pardus 1.1"

consts.log_file = "/tmp/install.log"

consts.data_dir = "/usr/share/yali"

consts.mnt_dir = "/mnt"

# new system will be installed directly into this target directory
consts.target_dir = join(consts.mnt_dir, "target")

# packages (and maybe others) will be in this source (cdrom) directory
consts.source_dir = join(consts.mnt_dir, "cdrom")

# comar socket path
consts.comar_socket_file = consts.target_dir + "/var/run/comar.socket"

# swap file path
consts.swap_file_name = ".swap"
consts.swap_file_path = join(consts.target_dir, 
                             consts.swap_file_name)

# user faces (for KDM)
consts.user_faces_dir = join(consts.data_dir, "user_faces")

# pisi repository
consts.cd_repo_name = "pardus-cd"
consts.cd_repo_uri = join(consts.source_dir, "repo/pisi-index.xml")

# pardus repository
consts.pardus_repo_name = "pardus-1"
consts.pardus_repo_uri = "http://paketler.uludag.org.tr/pardus-1/pisi-index.xml.bz2"

# min root partition size
consts.min_root_size = 3500

try:
    consts.lang = locale.getlocale()[0][:2]
except:
    # default lang to en_US
    consts.lang = "en"
