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

import os
import glob
import zipfile
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import pisi.ui

import yali.util
import yali.sysutils
import yali.pisiiface
import yali.postinstall
import yali.localeutils
from yali.constants import consts
import yali.context as ctx
from yali.gui.descSlide import slideDesc
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.installwidget import Ui_InstallWidget
from yali.gui.YaliDialog import QuestionDialog, EjectAndRetryDialog

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
    title = _("Installing Pardus")
    icon = "iconInstall"
    help = _('''
<font size="+2">Installation</font>

<font size="+1">

<p>
YALI is now installing Pardus on your computer. This operation takes
approximately 20-30 minutes depending on your computer's hardware.
</p>
<p>
Note that the installation from a USB storage will be much faster than
an optical medium (CD/DVD).
</p>
<p>
Now, sit back and enjoy the installation during which you will be able
to discover the features and the innovations offered by this new Pardus release.
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
        ctx.logger.debug("PkgInstaller is creating...")
        self.pkg_installer = PkgInstaller()
        ctx.logger.debug("Calling PkgInstaller.start...")
        self.pkg_installer.start()
        ctx.yali.info.updateAndShow(_("Installing packages..."))

        ctx.mainScreen.disableNext()
        ctx.mainScreen.disableBack()

        # start 30 seconds
        self.timer.start(1000 * 30)

    def customEvent(self, qevent):

        # EventPisi
        if qevent.eventType() == EventPisi:
            p, event = qevent.data()

            if event == pisi.ui.installing:
                self.ui.info.setText(_("Installing <b>%s</b><br>%s") % (p.name, p.summary))
                ctx.logger.debug("Pisi: %s installing" % p.name)
                self.cur += 1
                self.ui.progress.setValue(self.cur)
            elif event == pisi.ui.configuring:
                self.ui.info.setText(_("Configuring <b>%s</b>") % p.name)
                ctx.logger.debug("Pisi: %s configuring" % p.name)
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
                                                       _("Failed installing <b>%s</b>") % package,
                                                       _("Do you want to retry?"))

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

        ctx.yali.info.updateAndShow(_("Creating base layout..."))
        yali.postinstall.initbaselayout()

        # postscripts depend on 03locale...
        yali.localeutils.writeLocaleFromCmdline()

        #Write InitramfsConf
        yali.postinstall.writeInitramfsConf()

        # run dbus in chroot
        yali.util.start_dbus()

        ctx.yali.info.updateMessage(_("Configuring packages..."))

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
        import yali
        import yali.gui.runner

        self.hasErrors = True
        err_str = _("""An error occured during the installation of packages.

This may be caused by a corrupted installation medium.

Error:
%s
""") % str(e)

        yali.gui.runner.showException(yali.exception_fatal, err_str)

class PkgInstaller(QThread):

    def __init__(self):
        ctx.logger.debug("PkgInstaller started.")
        QThread.__init__(self)

    def run(self):
        ctx.logger.debug("PkgInstaller is running.")
        ui = PisiUI()
        ctx.logger.debug("PisiUI is creating..")
        yali.pisiiface.initialize(ui)
        ctx.logger.debug("Pisi initialize is calling..")

        # if exists use remote source repo
        # otherwise use cd as repo
        if ctx.installData.repoAddr:
            yali.pisiiface.addRemoteRepo(ctx.installData.repoName,ctx.installData.repoAddr)
        elif yali.sysutils.checkYaliParams(param=ctx.consts.dvd_install_param):
            yali.pisiiface.addRepo(ctx.consts.dvd_repo_name, ctx.installData.autoInstallationCollection.index)
            ctx.logger.debug("DVD Repo adding..")
            # Get only collection packages with collection Name
            order = yali.pisiiface.getAllPackagesWithPaths(collectionIndex=ctx.installData.autoInstallationCollection.index, ignoreKernels=True)
            kernelPackages = yali.pisiiface.getNeededKernel(ctx.installData.autoInstallationKernel, ctx.installData.autoInstallationCollection.index)
            order.extend(kernelPackages)
        else:
            ctx.logger.debug("CD Repo adding..")
            yali.pisiiface.addCdRepo()
            # Check for just installing system.base packages
            if yali.sysutils.checkYaliParams(param=ctx.consts.base_only_param):
                order = yali.pisiiface.getBasePackages()
            else:
                order = yali.pisiiface.getAllPackagesWithPaths()

            # Check for extra languages
            if not ctx.installData.installAllLangPacks:
                order = list(set(order) - set(yali.pisiiface.getNotNeededLanguagePackages()))
                ctx.logger.debug("Not needed lang packages will not be installing...")
                ctx.logger.debug(yali.pisiiface.getNotNeededLanguagePackages())


        # show progress
        total = len(order)
        ctx.logger.debug("Creating PisiEvent..")
        qevent = PisiEvent(QEvent.User, EventSetProgress)
        ctx.logger.debug("Setting data on just created PisiEvent (EventSetProgress)..")
        qevent.setData(total * 2)
        ctx.logger.debug("Posting PisiEvent to the widget..")
        objectSender(qevent)
        ctx.logger.debug("Found %d packages in repo.." % total)
        try:
            while True:
                try:
                    yali.pisiiface.install(order)
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

        ctx.logger.debug("Package install finished ...")
        # Package Install finished lets configure them
        qevent = PisiEvent(QEvent.User, EventPackageInstallFinished)
        objectSender(qevent)

class PkgConfigurator(QThread):

    def __init__(self):
        ctx.logger.debug("PkgConfigurator started.")
        QThread.__init__(self)

    def run(self):
        ctx.logger.debug("PkgConfigurator is running.")
        ui = PisiUI()
        yali.pisiiface.initialize(ui=ui, with_comar=True)

        try:
            # run all pending...
            ctx.logger.debug("exec : yali.pisiiface.configurePending() called")
            yali.pisiiface.configurePending()
        except Exception, e:
            # User+10: error
            qevent = PisiEvent(QEvent.User, EventError)
            qevent.setData(e)
            objectSender(qevent)

        # Remove cd repository and install add real
        if yali.sysutils.checkYaliParams(param=ctx.consts.dvd_install_param):
            yali.pisiiface.switchToPardusRepo(ctx.consts.dvd_repo_name)
        else:
            yali.pisiiface.switchToPardusRepo(ctx.consts.cd_repo_name)

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

