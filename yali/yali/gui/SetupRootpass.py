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


from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.rootpasswidget import RootPassWidget
import yali.users
import yali.sysutils
import yali.gui.context as ctx


##
# Root password widget
class Widget(RootPassWidget, ScreenWidget):

    help = _('''
<font size="+2">System administrator password and hostname</font>

<font size="+1">

<p>Please give a password for the system administrator (i.e root) for your
system. This password should be unique and private, as it is used to 
manage your desktop. Choose a password difficult to guess, but easy
to remember. 
</p>
<p>
The password may include upper and lower case characters, numbers and 
punctuation marks. Do not use Turkish characters or accents, as they
may impose some problems.
</p>

<p>
And also set the name that the computer will be identified to the network it belongs. The hostname should be descriptive enough to describe the computer.  
</p>

<p>
Click Next button to proceed.
</p>
</font>
''')

    def __init__(self, *args):
        apply(RootPassWidget.__init__, (self,) + args)
        
        self.host_valid = True
        self.pass_valid = True

        self.pix.setPixmap(ctx.iconfactory.newPixmap("admin"))
        self.pass_error.setText("")
        self.host_error.setText("")

        self.connect(self.pass1, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.pass2, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)

        self.connect(self.pass2, SIGNAL("returnPressed()"),
                     self.slotReturnPressed)

        self.connect(self.hostname, SIGNAL("textChanged(const QString &)"),
                     self.slotHostnameChanged)


    def shown(self):
        ctx.screens.disablePrev()

    def execute(self):
        user = yali.users.User("root")
        user.changePasswd(self.pass1.text().ascii())

        yali.sysutils.add_hostname(self.hostname.text().ascii())

        return True

    def slotTextChanged(self):

        p1 = self.pass1.text()
        p2 = self.pass2.text()

        if p1 == p2 and p1:
            # Sould we also check password length?
            self.pass_error.setText("")
            self.pass_valid = True
        else:
            self.pass_valid = False
            if p2:
                self.pass_error.setText(
                    _('<font color="#FF6D19">Passwords do not match!</font>'))
                self.pass_error.setAlignment(QLabel.AlignCenter)


        self.setNext()

    ##
    # check hostname validity
    def slotHostnameChanged(self, string):
        self.host_valid = yali.sysutils.text_is_valid(string.ascii())

        if not self.host_valid:
            self.host_error.setText(
                _('<font color="#FF6D19">Hostname contains invalid characters!</font>'))
        else:
            self.host_error.setText("")

        self.setNext()


    def setNext(self):
        if self.host_valid and self.pass_valid:
            ctx.screens.enableNext()
        else:
            ctx.screens.disableNext()


    def slotReturnPressed(self):
        if ctx.screens.isNextEnabled():
            ctx.screens.next()

