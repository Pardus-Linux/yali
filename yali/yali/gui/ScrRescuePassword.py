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
import pardus.xorg
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, QEvent, QObject

import yali.storage
import yali.pisiiface
import yali.postinstall
import yali.sysutils

from yali.gui.installdata import *
from yali.gui.YaliDialog import InfoDialog
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.rescuepasswordwidget import Ui_RescuePasswordWidget
from yali.gui.YaliSteps import YaliSteps
from yali.gui.GUIException import GUIException
from yali.gui.GUIAdditional import ConnectionWidget
import yali.gui.context as ctx

##
# BootLoader screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Reset Forgotten Passwords")
    icon = "iconInstall"
    help = _("""
<font size="+2">Password Recovery</font>
<font size="+1">
<p>
Here you can reset..
</p>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_RescuePasswordWidget()
        self.ui.setupUi(self)

        self.ui.pass_error.setVisible(False)
        self.ui.caps_error.setVisible(False)
        self.ui.caps_error.setText(_('Caps Lock is on.'))

        self.ui.updatePassword.setEnabled(False)

        self.steps = YaliSteps()
        self.steps.setOperations([{"text":_("Starting D-Bus..."),"operation":yali.sysutils.chrootDbus},
                                  {"text":_("Connecting to D-Bus..."),"operation":yali.postinstall.connectToDBus},
                                  {"text":_("Acquiring users..."),"operation":self.fillUserList}])

        self.connect(self.ui.updatePassword, SIGNAL("clicked()"), self.updatePassword)
        self.connect(self.ui.userList, SIGNAL("itemChanged(QListWidgetItem*)"),
                     self.resetWidgets)
        self.connect(self.ui.pass1, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.pass2, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)

    def resetWidgets(self):
        self.ui.pass1.clear()
        self.ui.pass2.clear()
        self.ui.updatePassword.setEnabled(False)

    def showError(self,message):
        self.ui.pass_error.setText("<center>%s</center>" % message)
        self.ui.pass_error.setVisible(True)
        self.ui.updatePassword.setEnabled(False)

    def checkCapsLock(self):
        if pardus.xorg.capslock.isOn():
            self.ui.caps_error.setVisible(True)
        else:
            self.ui.caps_error.setVisible(False)

    def keyReleaseEvent(self, e):
        self.checkCapsLock()

    def updatePassword(self):
        password = unicode(self.ui.pass1.text())
        uid  = int(self.ui.userList.currentItem().getInfo()[0])
        yali.postinstall.setUserPass(uid, password)
        InfoDialog(_("The password has been successfully reset."), title = _("Info"))
        self.resetWidgets()

    def slotTextChanged(self):
        p1 = self.ui.pass1.text()
        p2 = self.ui.pass2.text()
        if not self.ui.userList.currentItem():
            return
        user = self.ui.userList.currentItem().getInfo()
        if not p1 == '' and (str(p1).lower() == str(user[1]).lower() or \
                str(p1).lower() == str(user[2]).lower()):
            self.showError(_('Do not use your username or real name as your password.'))
            return
        elif p2 != p1 and p2:
            self.showError(_('The passwords do not match.'))
            return
        elif len(p1) == len(p2) and len(p2) < 4 and not p1=='':
            self.showError(_('Password is too short.'))
            return
        elif p1 == '' or p2 == '':
            self.ui.pass_error.setVisible(False)
            return
        else:
            self.ui.pass_error.setVisible(False)
            self.ui.updatePassword.setEnabled(True)

    def shown(self):
        ctx.mainScreen.disableBack()
        ctx.yali.info.show()
        self.steps.slotRunOperations()
        ctx.yali.info.hide()

    def fillUserList(self):
        users = yali.postinstall.getUserList()
        for user in users:
            UserItem(self.ui.userList, user)

    def execute(self):
        return True

    def backCheck(self):
        ctx.mainScreen.moveInc = 3
        return True

class UserItem(QtGui.QListWidgetItem):
    def __init__(self, parent, user):

        name = user[2]
        icon = "normal"
        if user[2] == "root":
            icon = "root"
            name = _("Super User")

        QtGui.QListWidgetItem.__init__(self, QtGui.QIcon(":/gui/pics/user_%s.png" % icon),
                                             "%s (%s)" % (name,user[1]),
                                             parent)
        self._user = user

    def getInfo(self):
        return self._user

