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


# PiSİ module for YALI

import os
import time

import comar
import pisi
import pisi.api
import pisi.config

import yali.postinstall
from yali.constants import consts


def initialize(ui, with_comar=False, ignore_dependency=False):

    options = pisi.config.Options()
    options.destdir = consts.target_dir
    options.yes_all = True
    # giving "comar = false" isn't enough for pisi 
    if with_comar:
        # wait for chroot_comar to initialize
        # generally we don't need this but I think this is safer
        for i in range(20):
            try:
                comar.Link(sockname=consts.comar_socket_file)
                break
            except:
                time.sleep(1)
                print "wait comar for 1 second..."

        pisi.api.init(options = options, comar = with_comar, database = True, ui = ui,
                      comar_sockname=consts.comar_socket_file, signal_handling = False)
    else:
        options.ignore_comar = True

        pisi.api.init(options = options, comar = with_comar, database = True, ui = ui,
		      signal_handling = False)

def add_repo(name, uri):
    print "add",name,uri
    pisi.api.add_repo(name, uri)

def update_repo(name):
    print "update repo", name
    pisi.api.update_repo(consts.cd_repo_name)

def remove_repo(name):
    print "remove", name
    pisi.api.remove_repo(name)

def finalize():
    pisi.api.finalize()

def install(pkg_name_list):
    pisi.api.install(pkg_name_list)

def install_all():
    install(get_available())

def get_available():
    import pisi.context as ctx
    l = ctx.packagedb.list_packages()

    return l

def get_available_len():
    return len(get_available())

def get_pending():
    import pisi.context as ctx

    l = ctx.installdb.list_pending()
    return l

def get_pending_len():
    return len(get_pending())
    

def configure_pending():
    print "configure pending postinstall"

    # dirty hack for COMAR to find scripts.
    os.symlink("/",
               consts.target_dir + consts.target_dir)

    pisi.api.configure_pending()

    os.unlink(consts.target_dir + consts.target_dir)
