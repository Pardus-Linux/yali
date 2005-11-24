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


import yali.users
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.setupuserswidget import SetupUsersWidget
import yali.gui.context as ctx

##
# Partitioning screen.
class Widget(SetupUsersWidget, ScreenWidget):

    help = _('''
<font size="+2">User setup</font>

<font size="+1">
<p>
Other than the system administrator user,
you can create a user account for your 
daily needs, i.e reading your e-mail, surfing
on the web and searching for daily recipe
offerings. Usual password assignment
rules also apply here: This password should 
be unique and private. Choose a password 
difficult to guess, but easy to remember. 
</p>
<p>
Click Next button to proceed.
</p>
</font>
''')

    def __init__(self, *args):
        apply(SetupUsersWidget.__init__, (self,) + args)

        self.pass_error.setText("")
        self.createButton.setEnabled(False)

        self.connect(self.pass1, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.pass2, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.username, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)

        self.connect(self.createButton, SIGNAL("clicked()"),
                     self.slotCreateUser)

        self.connect(self.deleteButton, SIGNAL("clicked()"),
                     self.slotDeleteUser)


    def shown(self):
        ctx.screens.prevEnabled()

    def execute(self):
        for i in range(self.userList.count()):
            u = self.userList.item(i).getUser()
            u.addUser()

    def slotTextChanged(self):

        p1 = self.pass1.text()
        p2 = self.pass2.text()

        if p2 != p1 and p2:
            self.pass_error.setText(
                _('<font color="#ff0000">Passwords do not match!</font>'))
            self.pass_error.setAlignment(QLabel.AlignCenter)
            return self.createButton.setEnabled(False)
        else:
            self.pass_error.setText("")


        if self.username.text() and self.pass1.text():
            self.createButton.setEnabled(True)
        else:
            self.createButton.setEnabled(False)

    def slotCreateUser(self):
        u = yali.users.User()
        u.username = self.username.text().ascii()
        u.realname = self.realname.text().ascii()
        u.passwd = self.pass1.text().ascii()
        u.groups = ["users", "audio", "video", "haldaemon", "plugdev", "wheel"]

        i = UserItem(self.userList, user = u)

        # clear all
        self.username.clear()
        self.pass1.clear()
        self.pass2.clear()

        self.checkUsers()


    def slotDeleteUser(self):
        self.userList.removeItem(self.userList.currentItem())
        self.checkUsers()

    def checkUsers(self):
        if self.userList.count():
            ctx.screens.nextEnabled()
        else:
            ctx.screens.nextDisabled()


class UserItem(QListBoxText):

    ##
    # @param user (yali.users.User)
    def __init__(self, parent, user):
        apply(QListBoxText.__init__, (self,parent,user.username))
        self._user = user
    
    def getUser(self):
        return self._user

