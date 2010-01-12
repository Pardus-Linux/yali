# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import dbus
import pisi
import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, QEvent, QObject

import yali4.storage
import yali4.pisiiface
import yali4.postinstall
import yali4.sysutils

from yali4.gui.installdata import *
from yali4.gui.GUIAdditional import DeviceItem
from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.Ui.rescuepisiwidget import Ui_RescuePisiWidget
from yali4.gui.YaliSteps import YaliSteps
from yali4.gui.GUIException import GUIException
from yali4.gui.GUIAdditional import ConnectionWidget
import yali4.gui.context as ctx

##
# BootLoader screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Rescue Mode for Pisi History')
    desc = _('You can take back your system ...')
    icon = "iconInstall"
    help = _('''
<font size="+2">Pisi History</font>
<font size="+1"></font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_RescuePisiWidget()
        self.ui.setupUi(self)
        self.steps = YaliSteps()
        self.steps.setOperations([{"text":_("Starting DBUS..."),"operation":yali4.sysutils.chrootDbus},
                                  {"text":_("Trying to connect DBUS..."),"operation":yali4.postinstall.connectToDBus},
                                  {"text":_("Getting history ..."),"operation":self.fillHistoryList}])

        self.connect(self.ui.buttonSelectConnection, SIGNAL("clicked()"), self.showConnections)
        self.connectionWidget = None

    def showConnections(self):
        self.connectionWidget.show()

    def fillHistoryList(self):
        ui = PisiUI()
        ctx.debugger.log("PisiUI is creating..")
        yali4.pisiiface.initialize(ui, with_comar = True)
        try:
            history = yali4.pisiiface.getHistory()
            for hist in history:
                HistoryItem(self.ui.historyList, hist)
        except:
            return False
        return True

    def checkRegisteredConnections(self):
        self.connectionWidget = ConnectionWidget(self)
        registeredConnectionsTotal = 0
        for connection in self.connectionWidget.connections.values():
            registeredConnectionsTotal+=len(connection)

        return registeredConnectionsTotal

    def shown(self):
        self.ui.buttonSelectConnection.setEnabled(False)
        ctx.yali.info.show()
        self.steps.slotRunOperations()
        ctx.yali.info.hide()
        if self.checkRegisteredConnections():
            self.ui.buttonSelectConnection.setEnabled(True)
        else:
            self.ui.labelStatus.setText(_("There is no connection"))

    def execute(self):
        ctx.takeBackOperation = self.ui.historyList.currentItem().getInfo()
        ctx.mainScreen.moveInc = 2
        return True

    def backCheck(self):
        ctx.mainScreen.moveInc = 2
        return True

class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)

    def notify(self, event, **keywords):
        ctx.debugger.log("PISI: Event %s %s" % (event, keywords))

    def display_progress(self, operation, percent, info, **keywords):
        ctx.debugger.log("PISI: %s %s %s" % (operation, percent, info))
        ctx.mainScreen.processEvents()

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

class HistoryItem(QtGui.QListWidgetItem):
    def __init__(self, parent, info):
        QtGui.QListWidgetItem.__init__(self, _("Operation %s : %s - %s") % (info.no, info.date, info.type), parent)
        self._info = info

    def getInfo(self):
        return self._info

