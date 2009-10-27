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

import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.Ui.rootpasswidget import Ui_RootPassWidget
import yali4.users
import yali4.sysutils
import yali4.gui.context as ctx
import pardus.xorg

##
# Root password widget
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Set Administrator')
    desc = _('Admins have important rights on the system...')
    icon = "iconAdmin"
    help = _('''
<font size="+2">System administrator password and hostname</font>

<font size="+1">
<p>
You need to define a password for the "root" user that has full control over the system.
Your password must be easy to remember (for you) but hard to guess (for others). 
You can use lower case or upper case letters, numbers and punctuation marks in your password. 
You should take care not to use letters not found in English to avoid incompatibilities with other systems.
</p>
<p>
Here you can enter a name for your computer in the text box below. As your computer will be 
known with this name in the local network, it is advised to enter a descriptive text.
Proceed with the installation after you make your selections.
</p>
<p>
Click Next button to proceed.
</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_RootPassWidget()
        self.ui.setupUi(self)

        self.host_valid = True
        self.pass_valid = False

        self.ui.pass_error.setVisible(False)
        self.ui.host_error.setVisible(False)
        self.ui.caps_error.setVisible(False)

        self.ui.caps_error.setText(_('<center>Caps Lock is on!</center>'))

        self.connect(self.ui.pass1, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.pass2, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.pass2, SIGNAL("returnPressed()"),
                     self.slotReturnPressed)
        self.connect(self.ui.hostname, SIGNAL("textChanged(const QString &)"),
                     self.slotHostnameChanged)

    def shown(self):

        if ctx.installData.hostName:
            self.ui.hostname.setText(str(ctx.installData.hostName))
        else:
            # Use first added user's name as machine name if its exists
            hostname_guess = "pardus"
            if len(yali4.users.pending_users) > 0:
                hostname_guess = "%s-pardus" % yali4.users.pending_users[0].username
            else:
                ctx.debugger.log("No user defined in users screen..")
            if self.ui.hostname.text() == '':
                self.ui.hostname.setText(hostname_guess)

        if ctx.installData.rootPassword:
            self.ui.pass1.setText(ctx.installData.rootPassword)
            self.ui.pass2.setText(ctx.installData.rootPassword)

        self.setNext()
        self.checkCapsLock()
        self.ui.pass1.setFocus()

    def execute(self):
        ctx.installData.rootPassword = unicode(self.ui.pass1.text())
        ctx.installData.hostName = self.ui.hostname.text().toAscii()
        return True

    def checkCapsLock(self):
        if pardus.xorg.capslock.isOn():
            self.ui.caps_error.setVisible(True)
        else:
            self.ui.caps_error.setVisible(False)

    def keyReleaseEvent(self, e):
        self.checkCapsLock()

    def slotTextChanged(self):

        p1 = self.ui.pass1.text()
        p2 = self.ui.pass2.text()

        if p1 == p2 and p1:
            if len(p1)<4:
                self.ui.pass_error.setText(_('Password is too short!'))
                self.ui.pass_error.setVisible(True)
                self.pass_valid = False
            else:
                self.ui.pass_error.setVisible(False)
                self.pass_valid = True
        else:
            self.pass_valid = False
            if p2:
                self.ui.pass_error.setText(_('Passwords do not match!'))
                self.ui.pass_error.setVisible(True)
        if str(p1).lower()=="root" or str(p2).lower()=="root":
            self.pass_valid = False
            if p2:
                self.ui.pass_error.setText(_('Don\'t use your username as password !'))
                self.ui.pass_error.setVisible(True)
        if self.pass_valid:
            self.ui.pass_error.setVisible(False)

        self.setNext()

    ##
    # check hostname validity
    def slotHostnameChanged(self, string):

        if not string.toAscii():
            self.host_valid = False
            self.setNext()
            return

        self.host_valid = yali4.sysutils.isTextValid(string.toAscii())

        if not self.host_valid:
            self.ui.host_error.setVisible(True)
            self.ui.host_error.setText(_('Hostname contains invalid characters!'))
        else:
            self.ui.host_error.setVisible(False)
        self.setNext()

    def setNext(self):
        if self.host_valid and self.pass_valid:
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def slotReturnPressed(self):
        if ctx.mainScreen.isNextEnabled():
            ctx.mainScreen.slotNext()

