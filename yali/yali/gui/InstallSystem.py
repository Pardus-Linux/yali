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
import yali.postinstall
import yali.fstab
import yali.partitionrequest as request
from yali.gui.installwidget import InstallWidget
from yali.gui.ScreenWidget import ScreenWidget
import yali.gui.context as ctx


##
# Partitioning screen.
class Widget(InstallWidget, ScreenWidget):

    def __init__(self, *args):
        apply(InstallWidget.__init__, (self,) + args)

    def shown(self):
        PkgInstaller().start(self)

        ctx.screens.prevDisabled()
        ctx.screens.nextDisabled()
        # TODO: start slide show
        
    def slotNotify(self, parent, event, p):

        # FIXME: use logging
        if event == pisi.ui.installing:
            self.info.setText(u"Installing: %s (%s)" % (
                    p.name, p.summary))

    def execute(self):

        # fill fstab
        fstab = yali.fstab.Fstab()
        for req in ctx.partrequests:
            if req.requestType() == request.mountRequestType:
                p = req.partition()
                pt = req.partitionType()

                path = p.getPath()
                fs = pt.filesystem.name()
                mountpoint = pt.mountpoint
                opts = pt.mountoptions

                e = yali.fstab.FstabEntry(path, mountpoint, fs, opts)
                fstab.insert(e)

        fstab.close()

        # run postinstall
        yali.postinstall.run_all()


        # TODO: stop slide show

    def finished(self):
        # trigger next screen
        ctx.screens.next()


class PkgInstaller(threading.Thread):

    def start(self, widget):
        self._widget = widget
        threading.Thread.start(self)

    def run(self):
        # TESTING
        ui = PisiUI(notify_widget = self._widget)
        yali.pisiiface.initialize(ui)

        yali.pisiiface.install_all()
        yali.pisiiface.finalize()

        self._widget.finished()

class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, notify_widget, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)

        self.connect(self, PYSIGNAL("signalNotify"),
                     notify_widget.slotNotify)

    def notify(self, event, **keywords):
        self.emit(PYSIGNAL("signalNotify"), (self, event, keywords['package']))

