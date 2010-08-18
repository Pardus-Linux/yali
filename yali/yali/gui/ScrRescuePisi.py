# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 TUBITAK/UEKAE
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
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, QEvent, QObject

import yali.util
import yali.pisiiface
import yali.postinstall
import yali.context as ctx
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.rescuepisiwidget import Ui_RescuePisiWidget
from yali.gui.YaliSteps import YaliSteps
from yali.gui.GUIException import GUIException
from yali.gui.GUIAdditional import ConnectionWidget

##
# BootLoader screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Take Back Your System")
    icon = "iconInstall"
    help = _("""
<font size="+2">Pisi History</font>
<font size="+1">
<p>
Pisi, the package management system of Pardus, stores every operation in its history database. More technically speaking, every removal/installation/update operation
within Pisi is a point-in-time that the user may want to return back in case of a
serious problem or system inconsistency.
</p>
<p>
This repair mode allows users to visualize the operation history and to return back to
a previous system state.
</p>
</font>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_RescuePisiWidget()
        self.ui.setupUi(self)
        self.steps = YaliSteps()
        self.steps.setOperations([{"text":_("Starting D-Bus..."),"operation":yali.util.start_dbus},
                                  {"text":_("Connecting to D-Bus..."),"operation":yali.postinstall.connectToDBus},
                                  {"text":_("Fetching history..."),"operation":self.fillHistoryList}])

        self.connect(self.ui.buttonSelectConnection, SIGNAL("clicked()"), self.showConnections)
        self.connectionWidget = None

    def showConnections(self):
        self.connectionWidget.show()

    def fillHistoryList(self):
        ui = PisiUI()
        ctx.logger.debug("PisiUI is creating..")
        yali.pisiiface.initialize(ui, with_comar = True)
        try:
            history = yali.pisiiface.getHistory()
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
            self.ui.labelStatus.setText(_("No connection available"))

    def execute(self):
        ctx.takeBackOperation = self.ui.historyList.currentItem().getInfo()
        ctx.mainScreen.stepIncrement = 2
        return True

    def backCheck(self):
        ctx.mainScreen.stepIncrement = 2
        return True

class PisiUI(QObject, pisi.ui.UI):

    def __init__(self, *args):
        pisi.ui.UI.__init__(self)
        apply(QObject.__init__, (self,) + args)

    def notify(self, event, **keywords):
        ctx.logger.debug("PISI: Event %s %s" % (event, keywords))

    def display_progress(self, operation, percent, info, **keywords):
        ctx.logger.debug("PISI: %s %s %s" % (operation, percent, info))
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

