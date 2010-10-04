# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
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
from os.path import exists
from yali.options import options

class _constant:
    """ Constant members implementation """
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
    """ YALI's Constants """
    __c = _constant()

    def __getattr__(self, attr):
        return getattr(self.__c, attr)

    def __setattr__(self, attr, value):
        setattr(self.__c, attr, value)

    def __delattr__(self, attr):
        delattr(self.__c, attr)

consts = Constants()

consts.pardus_version = file("/etc/pardus-release").readlines()[0].strip()

consts.data_dir = "/usr/share/yali"

consts.mnt_dir = "/mnt"

consts.tmp_mnt_dir = "/tmp/check"

if options.firstBoot == True or exists("/etc/yali-is-firstboot"):
    consts.target_dir = "/"
else:
    # new system will be installed directly into this target directory
    consts.target_dir = join(consts.mnt_dir, "target")

# log file for storing after installation
consts.log_file = join(consts.target_dir,"var/log/yaliInstall.log")

# session file for storing after installation
consts.session_file = join(consts.target_dir,"root/kahyaSession.xml")

# packages (and maybe others) will be in this source (cdrom) directory
consts.source_dir = join(consts.mnt_dir, "cdrom")

# dbus socket path
consts.dbus_socket_file = join(consts.target_dir, "var/run/dbus/system_bus_socket")

# swap file path
consts.swap_file_name = ".swap"
consts.swap_file_path = join(consts.target_dir, 
                             consts.swap_file_name)

# user faces (for KDM)
consts.user_faces_dir = join(consts.data_dir, "user_faces")

# pisi repository
consts.cd_repo_name = "pardus-cd"
consts.cd_repo_uri = join(consts.source_dir, "repo/pisi-index.xml.bz2")

# pardus repository
consts.pardus_repo_name = "pardus-2009"
consts.pardus_repo_uri = "http://packages.pardus.org.tr/pardus-2009/pisi-index.xml.bz2"
consts.pardus_release_path = "etc/pardus-release"

# min root partition size
consts.min_root_size = 3500

# kahya options
consts.kahya_param = "kahya"
consts.default_kahya_file = join(consts.data_dir,"data/default.xml")

# oem install options
consts.oem_install_param = "oeminstall"
consts.oem_install_file = join(consts.data_dir,"data/firstBoot.xml")

# rescue mode parameter for cmdline
consts.rescue_mode_param = "rescue"

# system.base packages only parameter for cmdline
consts.base_only_param = "baseonly"

# pisi index files
consts.dvd_repo_name = "pardus-dvd"
consts.dvd_install_param = "dvdinstall"
consts.pisi_index_file = join(consts.data_dir,"data/pisi-index.xml.bz2")
consts.pisi_index_file_sum = join(consts.data_dir,"data/pisi-index.xml.bz2.sha1sum")

# pisi collection index file
consts.pisi_collection_file = join(consts.data_dir, "data/index/collection.xml")
consts.pisi_collection_dir = join(consts.data_dir, "data/index")

# slideshows
consts.slidepics_dir = join(consts.data_dir, "slideshow")

try:
    consts.lang = locale.getdefaultlocale()[0][:2]
except:
    # default lang to en_US
    consts.lang = "en"

consts.MAX_PART_SIZE = 1024*1024*1024
