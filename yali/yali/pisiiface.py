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

import pisi
import pisi.api
import pisi.config

from yali.constants import consts


def initialize(ui):

    options = pisi.config.Options()
    options.destdir = consts.target_dir
    options.yes_all = True
    options.bypass_ldconfig = True
    # giving "comar = false" isn't enough for pisi 
    options.ignore_comar = True

    pisi.api.init(options = options, comar = False, database = True, ui = ui)

    add_repo(consts.repo_name, consts.repo_uri)

    pisi.api.update_repo(consts.repo_name)

def add_repo(name, uri):
    pisi.api.add_repo(name, uri)

def remove_repo(name):
    pisi.api.remove_repo(name)

def finalize():
    pisi.api.finalize()

def install(pkg_name_list):
    pisi.api.install(pkg_name_list)

def install_all():
    from pisi import packagedb
    
    pkg_db = packagedb.get_db(consts.repo_name)
    l = pkg_db.list_packages()
    install(l)
