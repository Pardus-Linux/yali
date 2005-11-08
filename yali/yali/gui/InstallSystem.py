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

import threading
from os.path import join
from qt import *

import pisi.ui

import yali.pisiiface
from yali.gui.installwidget import InstallWidget
from yali.gui.ScreenWidget import ScreenWidget
import yali.gui.context as ctx


##
# Partitioning screen.
class Widget(InstallWidget, ScreenWidget):

    def __init__(self, *args):
        apply(InstallWidget.__init__, (self,) + args)

    def shown(self):
        PkgInstaller().start()
        


class PkgInstaller(threading.Thread):

    def run(self):
        # TESTING
        ui = PisiUI()
        yali.pisiiface.initialize(ui)
        packages_file = join(ctx.consts.data_dir, "packages.list")
        pkg_list = [x[:-1] for x in open(packages_file).readlines()]
        yali.pisiiface.install(pkg_list)
        yali.pisiiface.finalize()


class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)


    def notify(self, event, **keywords):

        # FIXME: signal all!
        if event == pisi.ui.installed:
            msg = 'Installed %s' % keywords['package'].name
        elif event == pisi.ui.removed:
            msg = 'Removed %s' % keywords['package'].name
        elif event == pisi.ui.upgraded:
            msg = 'Upgraded %s' % keywords['package'].name

        print msg, "  --  YALI"
