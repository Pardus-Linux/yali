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
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, SIGNAL, QPixmap, QCoreApplication, QEvent, QThread, QObject, QTimer, QApplication, QMutex, QWaitCondition

import pisi.ui

import yali.util
import yali.pisiiface
import yali.postinstall
import yali.context as ctx
from yali.gui import ScreenWidget
from yali.gui.Ui.installwidget import Ui_InstallWidget
from yali.gui.YaliDialog import EjectAndRetryDialog

EventPisi, EventSetProgress, EventError, EventAllFinished, EventPackageInstallFinished, EventRetry = range(1001, 1007)

current_object = None

def iter_slideshows():
    slideshows = []

    release_file = os.path.join(ctx.consts.branding_dir, ctx.flags.branding, ctx.consts.release_file)
    slideshows_content = yali.util.parse_branding_slideshows(release_file)

    for content in slideshows_content:
        slideshows.append({"picture":QPixmap(os.path.join(ctx.consts.branding_dir,
                                                    ctx.flags.branding,
                                                    ctx.consts.slideshows_dir,
                                                    content[0])), "description":content[1]})
    while True:
        for slideshow in slideshows:
            yield slideshow

def object_sender(pack):
    global current_object
    QCoreApplication.postEvent(current_object, pack)

class Widget(QWidget, ScreenWidget):
    name = "packageInstallation"

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_InstallWidget()
        self.ui.setupUi(self)

        self.timer = QTimer(self)
        QObject.connect(self.timer, SIGNAL("timeout()"), self.changeSlideshows)

        if ctx.consts.lang == "tr":
            self.ui.progress.setFormat("%%p")

        self.iter_slideshows = iter_slideshows()

        # show first pic
        self.changeSlideshows()

        self.total = 0
        self.cur = 0
        self.has_errors = False

        # mutual exclusion
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.retry_answer = False
        self.pkg_configurator = None
        self.pkg_installer = None

    def shown(self):
        # Disable mouse handler
        ctx.mainScreen.dontAskCmbAgain = True
        ctx.mainScreen.theme_shortcut.setEnabled(False)

        # Thread object
        global current_object
        current_object = self

        # start installer thread
        ctx.logger.debug("PkgInstaller is creating...")
        self.pkg_installer = PkgInstaller()
        ctx.logger.debug("Calling PkgInstaller.start...")
        self.pkg_installer.start()
        #ctx.interface.informationWindow.update(_("Installing packages..."))

        ctx.mainScreen.disableNext()
        ctx.mainScreen.disableBack()

        # start 30 seconds
        self.timer.start(1000 * 30)

    def customEvent(self, qevent):

        # EventPisi
        if qevent.eventType() == EventPisi:
            package, event = qevent.data()

            if event == pisi.ui.installing:
                self.ui.info.setText(_("Installing <b>%(name)s</b><br>%(summary)s") % {"name":package.name,
                                                                                       "summary":package.summary)}
                ctx.logger.debug("Pisi: %s installing" % package.name)
                self.cur += 1
                self.ui.progress.setValue(self.cur)
            elif event == pisi.ui.configuring:
                self.ui.info.setText(_("Configuring <b>%s</b>") % package.name)
                ctx.logger.debug("Pisi: %s configuring" % package.name)
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
            msg = qevent.data()
            self.timer.stop()
            self.retry_answer = EjectAndRetryDialog(_("Warning"),
                    _("Following error occured while installing packages:\n"
                      "<b>%s</b>") % msg, _("Do you want to retry?"))

            self.timer.start(1000 * 30)
            self.wait_condition.wakeAll()

        # EventAllFinished
        elif qevent.eventType() == EventAllFinished:
            ctx.logger.debug("EventAllFinished catched")
            self.finished()

    def changeSlideshows(self):
        slide = self.iter_slideshows.next()
        self.ui.pix.setPixmap(slide["picture"])
        if slide["description"].has_key(ctx.consts.lang):
            description = slide["description"][ctx.consts.lang]
        else:
            description = slide["description"]["en"]
        self.ui.desc.setText(description)

    def packageInstallFinished(self):
        yali.postinstall.fillFstab()

        # Configure Pending...
        # run baselayout's postinstall first

        #ctx.interface.informationWindow.update(_("Creating base layout..."))
        yali.postinstall.initbaselayout()

        # postscripts depend on 03locale...
        yali.util.writeLocaleFromCmdline()

        #Write InitramfsConf
        yali.postinstall.writeInitramfsConf()

        # run dbus in chroot
        yali.util.start_dbus()

        #ctx.interface.informationWindow.update(_("Configuring packages..."))

        # start configurator thread
        self.pkg_configurator = PkgConfigurator()
        self.pkg_configurator.start()

    def execute(self):
        # stop slide show
        self.timer.stop()
        return True

    def finished(self):
        if self.has_errors:
            return
        #ctx.interface.informationWindow.hide()
        # trigger next screen. will activate execute()
        ctx.mainScreen.slotNext()

    def installError(self, error):
        self.has_errors = True
        errorstr = _("""An error occured during the installation of packages.

This may be caused by a corrupted installation medium.

Error:
%s
""") % str(error)
        ctx.interface.exceptionWindow(1, errorstr)

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

        if ctx.flags.collection:
            ctx.logger.debug("DVD Repo adding..")
            yali.pisiiface.addRepo(ctx.consts.dvd_repo_name, ctx.installData.autoInstallationCollection.index)
            # Get only collection packages with collection Name
            order = yali.pisiiface.getAllPackagesWithPaths(collectionIndex=ctx.installData.autoInstallationCollection.index, ignoreKernels=True)
            kernel_packages = yali.pisiiface.getNeededKernel(ctx.installData.autoInstallationKernel, ctx.installData.autoInstallationCollection.index)
            order.extend(kernel_packages)
        else:
            ctx.logger.debug("CD Repo adding..")
            yali.pisiiface.addCdRepo()
            # Check for just installing system.base packages
            if ctx.flags.baseonly:
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
        object_sender(qevent)
        ctx.logger.debug("Found %d packages in repo.." % total)
        try:
            while True:
                try:
                    yali.pisiiface.install(order)
                    break # while

                except Exception, msg:
                    # Lock the mutex
                    self.mutex.lock()

                    # Send event for asking retry
                    qevent = PisiEvent(QEvent.User, EventRetry)

                    # Send error message
                    qevent.setData(str(msg))
                    object_sender(qevent)

                    # wait for the result
                    self.wait_condition.wait(self.mutex)
                    self.mutex.unlock()

                    if self.retry_answer == "no":
                        raise msg

        except Exception, msg:
            # User+10: error
            qevent = PisiEvent(QEvent.User, EventError)
            qevent.setData(msg)
            object_sender(qevent)

            # wait for the result
            self.wait_condition.wait(self.mutex)

        ctx.logger.debug("Package install finished ...")
        # Package Install finished lets configure them
        qevent = PisiEvent(QEvent.User, EventPackageInstallFinished)
        object_sender(qevent)

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
        except Exception, msg:
            # User+10: error
            qevent = PisiEvent(QEvent.User, EventError)
            qevent.setData(msg)
            object_sender(qevent)

        # Remove cd repository and install add real
        if ctx.flags.collection:
            yali.pisiiface.switchToPardusRepo(ctx.consts.dvd_repo_name)
        else:
            yali.pisiiface.switchToPardusRepo(ctx.consts.cd_repo_name)

        qevent = PisiEvent(QEvent.User, EventAllFinished)
        object_sender(qevent)

class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)
        self.last_package = ''

    def notify(self, event, **keywords):
        if event == pisi.ui.installing or event == pisi.ui.configuring:
            qevent = PisiEvent(QEvent.User, EventPisi)
            data = [keywords['package'], event]
            self.last_package = keywords['package'].name
            qevent.setData(data)
            object_sender(qevent)
        QApplication.processEvents()

    def display_progress(self, operation, percent, info, **keywords):
        pass

class PisiEvent(QEvent):

    def __init__(self, event_type, event):
        QEvent.__init__(self, event_type)
        self.event = event

    def eventType(self):
        return self.event

    def setData(self, data):
        self._data = data

    def data(self):
        return self._data


