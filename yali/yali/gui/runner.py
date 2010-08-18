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
import sys
from PyQt4 import QtGui
from PyQt4.QtCore import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.installer
import yali.util
import yali.sysutils
import yali.localedata
import yali.gui.context as ctx
from yali.storage import Storage
from yali.storage.bootloader import BootLoader
from yali.gui.debugger import DebuggerAspect
from yali.gui.YaliDialog import Dialog
from yali.gui.Ui.exception import Ui_Exception

#from yali.gui.logger import Debugger
#from yali.gui.logger import DebuggerAspect

# mainScreen
import YaliWindow
from yali.gui.installdata import *

##
# Runner creates main GUI components for installation...
class Runner:

    _window = None
    _app = None

    def __init__(self):

        # Qt Stuff
        ctx._app = self._app = QtGui.QApplication(sys.argv)
        desktop  = self._app.desktop()

        # Yali..
        self._window = YaliWindow.Widget()
        ctx.mainScreen = self._window

        # Check for firstBoot on installed system (parameters from options)
        install_type = YALI_INSTALL

        if ctx.options.firstBoot == True or os.path.exists("/etc/yali-is-firstboot"):
            install_type = YALI_FIRSTBOOT

        # check for dvd install
        if yali.sysutils.checkYaliParams(param=ctx.consts.dvd_install_param):
            install_type = YALI_DVDINSTALL

        # check for oem install
        if yali.sysutils.checkYaliParams(param=ctx.consts.oem_install_param):
            install_type = YALI_OEMINSTALL

        # check for rescue Mode
        if ctx.options.rescueMode == True or yali.sysutils.checkYaliParams(param=ctx.consts.rescue_mode_param):
            install_type = YALI_RESCUE

        install_plugin = yali.sysutils.checkYaliOptions("plugin") or ctx.options.plugin or None
        if install_plugin:
            install_type = YALI_PLUGIN

        # Creating the installer
        ctx.yali = yali.installer.Yali(install_type, install_plugin)

        ctx.storage = Storage()
        #ctx.storage.reset()
        ctx.bootloader = BootLoader()

        # These shorcuts for developers :)
        prevScreenShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.SHIFT + Qt.Key_F1),self._window)
        nextScreenShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.SHIFT + Qt.Key_F2),self._window)
        QObject.connect(prevScreenShortCut, SIGNAL("activated()"), self._window.slotBack)
        QObject.connect(nextScreenShortCut, SIGNAL("activated()"), self._window.slotNext)

        # check boot flags
        if ctx.options.debug == "True" or yali.sysutils.checkYaliParams(param="debug"):
            ctx.debugEnabled = True

        # Let start
        ctx.logger.debug("Yali has been started.")
        ctx.logger.debug("System language is '%s'" % ctx.consts.lang)
        ctx.logger.debug("Install type is %d" % ctx.yali.install_type)
        ctx.logger.debug("Kernel Command Line : %s" % file("/proc/cmdline","r").read())

        # VBox utils
        ctx.logger.debug("Starting VirtualBox tools..")
        yali.util.run_batch("VBoxClient", ["--autoresize"])
        yali.util.run_batch("VBoxClient", ["--clipboard"])

        # Cp Reboot, ShutDown
        yali.util.run_batch("cp", ["/sbin/reboot", "/tmp/reboot"])
        yali.util.run_batch("cp", ["/sbin/shutdown", "/tmp/shutdown"])

        # add Screens for selected install type
        self._window.createWidgets(ctx.yali.screens)

        # base connections
        QObject.connect(self._app, SIGNAL("lastWindowClosed()"),
                        self._app, SLOT("quit()"))
        QObject.connect(ctx.mainScreen, SIGNAL("signalProcessEvents"),
                        self._app.processEvents)
        QObject.connect(desktop, SIGNAL("resized(int)"),
                        self._reinit_screen)

        # set the current screen ...
        ctx.mainScreen.setCurrent(ctx.options.startupScreen)

        # Font Resize
        fontMinusShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_Minus),self._window)
        fontPlusShortCut  = QtGui.QShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_Plus) ,self._window)
        QObject.connect(fontMinusShortCut, SIGNAL("activated()"), self._window.setFontMinus)
        QObject.connect(fontPlusShortCut , SIGNAL("activated()"), self._window.setFontPlus)

    ##
    # Fire up the interface.
    def run(self):

        # Use default theme;
        # if you use different Qt4 theme our works looks ugly :)
        self._app.setStyle(QtGui.QStyleFactory.create('Plastique'))
        self._init_screen()

        # For testing..
        # self._window.resize(QSize(800,600))

        # Run run run
        self._app.exec_()

    def _reinit_screen(self):
        QTimer.singleShot(700,self._init_screen)

    def _init_screen(self, screen = 0):
        # We want it to be a full-screen window
        # inside the primary display.
        scr = self._app.desktop().screenGeometry()
        self._window.resize(scr.size())
        self._window.setMaximumSize(scr.size())
        self._window.move(scr.topLeft())
        self._window.show()
        ctx.yali.info.updateMessage()

def showException(ex_type, tb):
    title = _("An error occured")
    closeButton = True

    if ex_type in (yali.exception_fatal, yali.exception_pisi):
        closeButton = False

    ctx.logger.debug(tb)
    d = Dialog(title, ExceptionWidget(tb, not closeButton), None, closeButton, icon="error")
    d.resize(300,160)
    d.exec_()

class ExceptionWidget(QtGui.QWidget):
    def __init__(self, tb_text, rebootButton = False):
        QtGui.QWidget.__init__(self, None)
        self.ui = Ui_Exception()
        self.ui.setupUi(self)
        self.ui.info.setText(_("Unhandled exception occured"))
        self.ui.traceback.setText(tb_text)
        self.ui.traceback.hide()
        self.connect(self.ui.showBackTrace, SIGNAL("clicked()"), self.showBackTrace)
        self.connect(self.ui.rebootButton,  SIGNAL("clicked()"), yali.util.reboot)
        self.ui.rebootButton.setShown(rebootButton)

    def showBackTrace(self):
        self.ui.traceback.show()
        self.ui.showBackTrace.hide()
        self.emit(SIGNAL("resizeDialog(int,int)"), 440, 440)

