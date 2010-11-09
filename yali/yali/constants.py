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

import os
import locale

class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)

        return cls.instance


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
    __metaclass__ = Singleton

    __c = _constant()

    def __init__(self):
        self.__c.min_root_size = 3500
        self.__c.root_path = "/"
        self.__c.conf_file = "/etc/yali/yali.conf"
        self.__c.data_dir = "/usr/share/yali"
        self.__c.log_dir = "/var/log"
        self.__c.log_file = "yali.log"
        self.__c.target_dir = "/mnt/target"
        self.__c.source_dir = "/mnt/cdrom"
        self.__c.tmp_mnt_dir = "/tmp/check"
        self.__c.dbus_socket = os.path.join(self.__c.target_dir,"var/run/dbus/system_bus_socket")
        self.__c.slidepics_dir = os.path.join(self.__c.data_dir, "slideshow")
        self.__c.repo_uri = os.path.join(self.__c.source_dir, "repo/pisi-index.xml.bz2")
        self.__c.pisi_collection_file = os.path.join(self.__c.data_dir, "data/index/collection.xml")
        self.__c.pisi_collection_dir = os.path.join(self.__c.data_dir, "data/index")
        self.__c.cd_repo_name = "pardus-cd"
        self.__c.dvd_repo_name = "pardus-dvd"
        self.__c.cd_repo_uri = os.path.join(self.__c.source_dir, "repo/pisi-index.xml.bz2")
        self.__c.pardus_repo_name = "pardus-2009"
        self.__c.pardus_repo_uri = "http://packages.pardus.org.tr/pardus-2009/pisi-index.xml.bz2"
        self.__c.pisi_index_file = os.path.join(self.__c.data_dir,"data/pisi-index.xml.bz2")
        self.__c.pisi_index_file_sum = os.path.join(self.__c.data_dir,"data/pisi-index.xml.bz2.sha1sum")
        self.__c.session_file = os.path.join(self.__c.target_dir, "root/kahyaSession.xml")
        self.__c.default_kahya_file = os.path.join(self.__c.data_dir,"data/default.xml")
        self.__c.oem_install_file = os.path.join(self.__c.data_dir,"data/firstBoot.xml")
        self.__c.alternatestylesheet = os.path.join(self.__c.data_dir, "data/oxygen.qss")
        self.__c.lang = locale.getdefaultlocale()[0][:2]

    def __getattr__(self, attr):
        return getattr(self.__c, attr)

    def __setattr__(self, attr, value):
        setattr(self.__c, attr, value)

    def __delattr__(self, attr):
        delattr(self.__c, attr)


consts = Constants()
