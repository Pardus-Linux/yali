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
import yali.localedata
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

        ctx.screens.disableNext()
        ctx.screens.disablePrev()

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
            self.info.setText(_("Configuring package: %s") % p.name)
            
            self.cur += 1
            self.progress.setProgress(self.cur)

    def slotChangePix(self):
        self.pix.setPixmap(self.iter_pics.next())

    def execute(self):
        
        # fill fstab
        fstab = yali.fstab.Fstab()
        for req in ctx.partrequests:
            req_type = req.requestType()
            if req_type == request.mountRequestType:
                p = req.partition()
                pt = req.partitionType()

                path = p.getPath()
                fs = pt.filesystem.name()
                mountpoint = pt.mountpoint
                opts = pt.mountoptions

                e = yali.fstab.FstabEntry(path, mountpoint, fs, opts)
                fstab.insert(e)
            elif req_type == request.swapFileRequestType:
                path = "/" + ctx.consts.swap_file_name
                mountpoint = "none"
                fs = "swap"
                opts = "sw"
                e = yali.fstab.FstabEntry(path, mountpoint, fs, opts)
                fstab.insert(e)

        fstab.close()

        # Configure Pending...       
        yali.sysutils.chroot_comar() # run comar in chroot
        self.info.setText(_("Configuring packages for your system!"))
        # re-initialize pisi with comar this time.
        ui = PisiUI(notify_widget = self)
        yali.pisiiface.initialize(ui=ui, with_comar=True)
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


        # FIXME: I don't know if this is the right way to do
        # this. maybe postinstall can be used too.
        yali.localedata.write_locale_from_cmdline()
        yali.localedata.write_font_from_cmdline(ctx.keydata)


        return True

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

    def installError(self, e):
        #self.info.setText(str(e))
        import yali
        import yali.gui.runner

        err_str = _('''An error during the installation of packages occured.

This is possibly a broken Pardus CD or CD-ROM drive.

Error:
%s
''') % str(e)


        yali.gui.runner.showException(yali.exception_fatal, err_str)
        


class PkgInstaller(threading.Thread):

    def start(self, widget):
        self._widget = widget
        threading.Thread.start(self)

    def run(self):
        try:
            yali.pisiiface.install_all()
        except Exception, e:
            self._widget.installError(e)

        self._widget.finished()

class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, notify_widget, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)

        self.connect(self, PYSIGNAL("signalNotify"),
                     notify_widget.slotNotify)

    def notify(self, event, **keywords):
        if event == pisi.ui.installing or event == pisi.ui.configuring:
            self.emit(PYSIGNAL("signalNotify"),
                      (self, event, keywords['package']))

