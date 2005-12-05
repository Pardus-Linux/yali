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

import glob
import threading
import os
from os.path import join
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import pisi.ui

import yali.pisiiface
import yali.fstab
import yali.sysutils
import yali.partitionrequest as request
from yali.gui.installwidget import InstallWidget
from yali.gui.ScreenWidget import ScreenWidget
import yali.gui.context as ctx


def iter_slide_pics():
    # load all pics
    pics = []
    g = glob.glob(ctx.consts.slidepics_dir + "/*.png")
    g.sort()
    for p in g:
        pics.append(QPixmap(p))

    while True:
        for pic in pics:
            yield pic



##
# Partitioning screen.
class Widget(InstallWidget, ScreenWidget):

    help = _('''
<font size="+2">Installation started</font>

<font size="+1">

<p>
Pardus is now being installed on your hard disk. 
</p>

<p>
The duration of this operation depends on the 
capability and power of your system. Meanwhile,
you can enjoy some visual elements showing 
the distinctive properties of Pardus, your 
new operating system.
</p>

<p>
Have fun!
</p>
</font>
''')

    def __init__(self, *args):
        apply(InstallWidget.__init__, (self,) + args)

        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL("timeout()"),
                     self.slotChangePix)

        self.iter_pics = iter_slide_pics()

        # show first pic
        self.slotChangePix()

        self.total = 0
        self.cur = 0

    def shown(self):
        # initialize pisi
        ui = PisiUI(notify_widget = self)

        yali.pisiiface.initialize(ui)

        repo_name = ctx.consts.repo_name
        repo_uri = ctx.consts.repo_uri
        yali.pisiiface.add_repo(repo_name, repo_uri)
        yali.pisiiface.update_repo(repo_name)

        # show progress
        self.total = yali.pisiiface.get_available_len()
        self.progress.setTotalSteps(self.total)

        # start installer thread
        PkgInstaller().start(self)

        ctx.screens.prevDisabled()
        ctx.screens.nextDisabled()

        # start 30 seconds
        self.timer.start(1000 * 30)

        
    def slotNotify(self, parent, event, p):

        # FIXME: use logging
        if event == pisi.ui.installing:
            self.info.setText(_("Installing: %s<br>%s") % (
                    p.name, p.summary))

            self.cur += 1
            self.progress.setProgress(self.cur)
        elif event == pisi.ui.configuring:
            self.info.setText(_("Configuring package: %s" % p.name))
            
            self.cur += 1
            self.progress.setProgress(self.cur)

    def slotChangePix(self):
        self.pix.setPixmap(self.iter_pics.next())

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

        # Configure Pending...       
        yali.sysutils.chroot_comar() # run comar in chroot
        self.info.setText(_("Configuring packages for your system!"))
        # re-initialize pisi with comar this time.
        yali.pisiiface.initialize(ui=None, with_comar=True)
        # show progress
        self.cur = 0
        self.progress.setProgress(self.cur)
        self.total = yali.pisiiface.get_pending_len()
        self.progress.setTotalSteps(self.total)
        # run all pending...
        yali.pisiiface.configure_pending()
        yali.pisiiface.finalize()

        # FIXME: move to sysutils
        os.system("chroot /mnt/target /usr/bin/update-environ.py")

        # stop slide show
        self.timer.stop()

    def finished(self):
        # Remove cd repository and install add real
        repo_name = ctx.consts.repo_name # install repo on CD
        devel_repo_name = ctx.consts.devel_repo_name
        devel_repo_uri = ctx.consts.devel_repo_uri

        yali.pisiiface.remove_repo(repo_name)
        yali.pisiiface.add_repo(devel_repo_name, devel_repo_uri)

        yali.pisiiface.finalize()

        # trigger next screen
        ctx.screens.next()


class PkgInstaller(threading.Thread):

    def start(self, widget):
        self._widget = widget
        threading.Thread.start(self)

    def run(self):
        yali.pisiiface.install_all()

        self._widget.finished()

class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, notify_widget, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)

        self.connect(self, PYSIGNAL("signalNotify"),
                     notify_widget.slotNotify)

    def notify(self, event, **keywords):
        self.emit(PYSIGNAL("signalNotify"), (self, event, keywords['package']))

