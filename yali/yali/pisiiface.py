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

    pisi.api.init(options = options, comar = False, database = True, ui = ui)

    pisi.api.add_repo(consts.repo_name, consts.repo_uri)

    pisi.api.update_repo(consts.repo_name)


def finalize():
    pisi.api.finalize()

def install(pkg_name_list):
    pisi.api.install(pkg_name_list)

