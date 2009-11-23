# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import glob
import zipfile
import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import pisi.ui

import yali4.fstab
import yali4.sysutils
import yali4.pisiiface
import yali4.postinstall
import yali4.localeutils

import yali4.gui.context as ctx
import yali4.partitionrequest as request

from yali4.gui.descSlide import slideDesc
from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.YaliDialog import QuestionDialog, EjectAndRetryDialog
from yali4.gui.Ui.installwidget import Ui_InstallWidget

EventPisi, EventSetProgress, EventError, EventAllFinished, EventPackageInstallFinished, EventRetry = range(1001,1007)

def iter_slide_pics():
    def pat(pic):
        return "%s/%s.png" % (ctx.consts.slidepics_dir, pic)

    # load all pics
    pics = []

    for slide in slideDesc:
        pic, desc = slide.items()[0]
        pics.append({"pic":QtGui.QPixmap(pat(pic)),"desc":desc})

    while True:
        for pic in pics:
            yield pic

def objectSender(pack):
    global currentObject
    QCoreApplication.postEvent(currentObject, pack)

##
# Partitioning screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Installing system...')
    desc = _('Installing takes approximately 20 minutes depending on your hardware...')
    icon = "iconInstall"
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
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_InstallWidget()
        self.ui.setupUi(self)

        self.timer = QTimer(self)
        QObject.connect(self.timer, SIGNAL("timeout()"),self.slotChangePix)

        if ctx.consts.lang == "tr":
            self.ui.progress.setFormat("%%p")

        self.iter_pics = iter_slide_pics()

        # show first pic
        self.slotChangePix()

        self.total = 0
        self.cur = 0
        self.hasErrors = False

    def shown(self):
        # Disable mouse handler
        ctx.mainScreen.dontAskCmbAgain = True
        ctx.mainScreen.themeShortCut.setEnabled(False)

        # Thread object
        global currentObject
        currentObject = self

        # start installer thread
        ctx.debugger.log("PkgInstaller is creating...")
        self.pkg_installer = PkgInstaller()
        ctx.debugger.log("Calling PkgInstaller.start...")
        self.pkg_installer.start()
        ctx.yali.info.updateAndShow(_("Packages are being installed.."))

        ctx.mainScreen.disableNext()
        ctx.mainScreen.disableBack()

        # start 30 seconds
        self.timer.start(1000 * 30)

    def customEvent(self, qevent):

        # EventPisi
        if qevent.eventType() == EventPisi:
            p, event = qevent.data()

            if event == pisi.ui.installing:
                self.ui.info.setText(_("Installing: <b>%s</b><br>%s") % (p.name, p.summary))
                ctx.debugger.log("Pisi : %s installing" % p.name)
                self.cur += 1
                self.ui.progress.setValue(self.cur)
            elif event == pisi.ui.configuring:
                self.ui.info.setText(_("Configuring package: <b>%s</b>") % p.name)
                ctx.debugger.log("Pisi : %s configuring" % p.name)
                self.cur += 1
                self.ui.progress.setValue(self.cur)

        # EventSetProgress
        elif qevent.eventType() == EventSetProgress:
            total = qevent.data()
            self.ui.progress.setMaximum(total)

        # EventPackageInstallFinished
        elif qevent.eventType() == EventPackageInstallFinished:
            self.packageInstallFinished()

        # EventError
        elif qevent.eventType() == EventError:
            err = qevent.data()
            self.installError(err)

        # EventRetry
        elif qevent.eventType() == EventRetry:
            package = qevent.data()
            self.timer.stop()
            ctx.yali.retryAnswer = EjectAndRetryDialog(_("Warning"),
                                                       _("Package install failed : <b>%s</b>") % package,
                                                       _("Do you want to retry ?"))

            self.timer.start(1000 * 30)
            ctx.yali.waitCondition.wakeAll()

        # EventAllFinished
        elif qevent.eventType() == EventAllFinished:
            self.finished()

    def slotChangePix(self):
        slide = self.iter_pics.next()
        self.ui.pix.setPixmap(slide["pic"])
        self.ui.desc.setText(slide["desc"])

    def packageInstallFinished(self):

        ctx.yali.fillFstab()

        # Configure Pending...
        # run baselayout's postinstall first

        ctx.yali.info.updateAndShow(_("Creating baselayout for your system!"))
        yali4.postinstall.initbaselayout()

        # postscripts depend on 03locale...
        yali4.localeutils.writeLocaleFromCmdline()

        # run dbus in chroot
        yali4.sysutils.chrootDbus()

        ctx.yali.info.updateMessage(_("Configuring packages.."))

        # start configurator thread
        self.pkg_configurator = PkgConfigurator()
        self.pkg_configurator.start()

    def execute(self):
        # stop slide show
        self.timer.stop()
        return True

    def finished(self):
        if self.hasErrors:
            return
        ctx.yali.info.hide()
        # trigger next screen. will activate execute()
        ctx.mainScreen.slotNext()

    def installError(self, e):
        import yali4
        import yali4.gui.runner

        self.hasErrors = True
        err_str = _('''An error during the installation of packages occured.

This is possibly a broken Pardus CD or CD-ROM drive.

Error:
%s
''') % str(e)

        yali4.gui.runner.showException(yali4.exception_fatal, err_str)

class PkgInstaller(QThread):

    def __init__(self):
        ctx.debugger.log("PkgInstaller started.")
        QThread.__init__(self)

    def run(self):
        ctx.debugger.log("PkgInstaller is running.")
        ui = PisiUI()
        ctx.debugger.log("PisiUI is creating..")
        yali4.pisiiface.initialize(ui)
        ctx.debugger.log("Pisi initialize is calling..")

        # if exists use remote source repo
        # otherwise use cd as repo
        if ctx.installData.repoAddr:
            yali4.pisiiface.addRemoteRepo(ctx.installData.repoName,ctx.installData.repoAddr)
        elif yali4.sysutils.checkYaliParams(param=ctx.consts.dvd_install_param):
            yali4.pisiiface.addRepo(ctx.consts.dvd_repo_name, ctx.installData.autoInstallationCollection.index)
            ctx.debugger.log("DVD Repo adding..")
            # Get only collection packages with collection Name
            order = yali4.pisiiface.getAllPackagesWithPaths(collectionIndex=ctx.installData.autoInstallationCollection.index)
        else:
            ctx.debugger.log("CD Repo adding..")
            yali4.pisiiface.addCdRepo()
            # Check for just installing system.base packages
            if yali4.sysutils.checkYaliParams(param=ctx.consts.base_only_param):
                order = yali4.pisiiface.getBasePackages()
            else:
                order = yali4.pisiiface.getAllPackagesWithPaths()

            # Check for extra languages
            if not ctx.installData.installAllLangPacks:
                order = list(set(order) - set(yali4.pisiiface.getNotNeededLanguagePackages()))
                ctx.debugger.log("Not needed lang packages will not be installing...")
                ctx.debugger.log(yali4.pisiiface.getNotNeededLanguagePackages())


        # show progress
        total = len(order)
        ctx.debugger.log("Creating PisiEvent..")
        qevent = PisiEvent(QEvent.User, EventSetProgress)
        ctx.debugger.log("Setting data on just created PisiEvent (EventSetProgress)..")
        qevent.setData(total * 2)
        ctx.debugger.log("Posting PisiEvent to the widget..")
        objectSender(qevent)
        ctx.debugger.log("Found %d packages in repo.." % total)
        try:
            while True:
                try:
                    yali4.pisiiface.install(order)
                    break # while

                except zipfile.BadZipfile, e:
                    # Lock the mutex
                    ctx.yali.mutex.lock()

                    # Send event for asking retry
                    qevent = PisiEvent(QEvent.User, EventRetry)

                    # Send failed package name
                    qevent.setData(os.path.basename(str(e)))
                    objectSender(qevent)

                    # wait for the result
                    ctx.yali.waitCondition.wait(ctx.yali.mutex)
                    ctx.yali.mutex.unlock()

                    if ctx.yali.retryAnswer == "no":
                        raise e

                except Exception, e:
                    # Lock the mutex
                    ctx.yali.mutex.lock()
                    raise e

        except Exception, e:
            # Lock the mutex
            ctx.yali.mutex.lock()

            # User+10: error
            qevent = PisiEvent(QEvent.User, EventError)
            qevent.setData(e)
            objectSender(qevent)

            # wait for the result
            ctx.yali.waitCondition.wait(ctx.yali.mutex)

        ctx.debugger.log("Package install finished ...")
        # Package Install finished lets configure them
        qevent = PisiEvent(QEvent.User, EventPackageInstallFinished)
        objectSender(qevent)

class PkgConfigurator(QThread):

    def __init__(self):
        ctx.debugger.log("PkgConfigurator started.")
        QThread.__init__(self)

    def run(self):
        ctx.debugger.log("PkgConfigurator is running.")
        ui = PisiUI()
        yali4.pisiiface.initialize(ui=ui, with_comar=True)

        try:
            # run all pending...
            ctx.debugger.log("exec : yali4.pisiiface.configurePending() called")
            yali4.pisiiface.configurePending()
        except Exception, e:
            # User+10: error
            qevent = PisiEvent(QEvent.User, EventError)
            qevent.setData(e)
            objectSender(qevent)

        # Remove cd repository and install add real
        if yali4.sysutils.checkYaliParams(param=ctx.consts.dvd_install_param):
            yali4.pisiiface.switchToPardusRepo(ctx.consts.dvd_repo_name)
        else:
            yali4.pisiiface.switchToPardusRepo(ctx.consts.cd_repo_name)

        qevent = PisiEvent(QEvent.User, EventAllFinished)
        objectSender(qevent)

class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)
        self.lastPackage = ''

    def notify(self, event, **keywords):
        if event == pisi.ui.installing or event == pisi.ui.configuring:
            qevent = PisiEvent(QEvent.User, EventPisi)
            data = [keywords['package'], event]
            self.lastPackage = keywords['package'].name
            qevent.setData(data)
            objectSender(qevent)

    def display_progress(self, operation, percent, info, **keywords):
        pass

class PisiEvent(QEvent):

    def __init__(self, _, event):
        QEvent.__init__(self, _)
        self.event = event

    def eventType(self):
        return self.event

    def setData(self,data):
        self._data = data

    def data(self):
        return self._data

