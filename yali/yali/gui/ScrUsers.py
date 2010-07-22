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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import os
import yali.users
import pardus.xorg
import yali.gui.context as ctx

from PyQt4 import QtGui
from PyQt4.QtCore import *
from yali.constants import consts
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.setupuserswidget import Ui_SetupUsersWidget
from yali.gui.YaliDialog import Dialog

##
# Partitioning screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Add Users")
    icon = "iconUser"
    help = _('''
<font size="+2">System Users</font>
<font size="+1">
<p>
Pardus allows multiple users to share the same computer.
You can assign management rights to the users you create; you can also
configure permissions to users for various operations through User Manager.
</p>
<p>
To create a new user, fill in the form and press the "Create User" button.
If you want a user to be automatically logged in to the system, select
the user from the list; if you want to delete a user, 
select his/her username from the list and press "Delete Selected User".
Proceed with the installation after you make your selections.
</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_SetupUsersWidget()
        self.ui.setupUi(self)

        self.edititemindex = None

        self.ui.pass_error.setVisible(False)
        self.ui.caps_error.setVisible(False)

        self.ui.advancedList.setVisible(False)
        self.ui.createButton.setVisible(False)
        self.ui.cancelButton.setVisible(False)
        self.ui.userIDCheck.setVisible(False)
        self.ui.userID.setVisible(False)

        self.ui.caps_error.setText(_('Caps Lock is on.'))

        # User Icons
        self.normalUserIcon = QtGui.QPixmap(":/gui/pics/user_normal.png")
        self.superUserIcon = QtGui.QPixmap(":/gui/pics/user_root.png")

        # KDE AutoLogin
        self.autoLoginUser = ""

        # Set disabled the create Button
        self.ui.createButton.setEnabled(False)

        # Connections
        self.connect(self.ui.pass1, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.pass2, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.username, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.realname, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.username, SIGNAL("textEdited(const QString &)"),
                     self.slotUserNameChanged)
        self.connect(self.ui.realname, SIGNAL("textEdited(const QString &)"),
                     self.slotRealNameChanged)
        self.connect(self.ui.userID, SIGNAL("valueChanged(int)"),
                     self.slotTextChanged)
        self.connect(self.ui.createButton, SIGNAL("clicked()"),
                     self.slotCreateUser)
        self.connect(self.ui.cancelButton, SIGNAL("clicked()"),
                     self.resetWidgets)
        self.connect(self.ui.deleteButton, SIGNAL("clicked()"),
                     self.slotDeleteUser)
        self.connect(self.ui.editButton, SIGNAL("clicked()"),
                     self.slotEditUser)
        self.connect(self.ui.addMoreUsers, SIGNAL("clicked()"),
                     self.slotAdvanced)
        self.connect(self.ui.userList, SIGNAL("itemDoubleClicked(QListWidgetItem*)"),
                     self.slotEditUser)
        self.connect(self.ui.pass2, SIGNAL("returnPressed()"),
                     self.slotReturnPressed)

        ctx.installData.users = []
        ctx.installData.autoLoginUser = None
        self.userNameChanged = False
        self.usedIDs = []

    def shown(self):
        self.ui.cancelButton.hide()
        self.ui.realname.setFocus()
        if len(yali.users.pending_users) > 0 and self.ui.userList.count() == 0:
            for u in yali.users.pending_users:
                pix = self.normalUserIcon
                if "wheel" in u.groups:
                    pix = self.superUserIcon
                UserItem(self.ui.userList, pix, user = u)
                self.ui.autoLogin.addItem(QString(u.username))
        if len(yali.users.pending_users) == 1:
            self.slotEditUser(self.ui.userList.item(0))
        elif len(yali.users.pending_users) > 1:
            self.ui.addMoreUsers.setChecked(True)
        self.checkUsers()
        self.checkCapsLock()

    def backCheck(self):
        self.refill()
        self.ui.cancelButton.hide()
        return True

    def refill(self):
        # reset and fill pending_users
        yali.users.resetPendingUsers()
        for i in range(self.ui.userList.count()):
            u = self.ui.userList.item(i).getUser()
            ctx.installData.users.append(u)
            yali.users.pending_users.append(u)

    def execute(self):

        if self.checkUsers():
            self.refill()
            ctx.installData.autoLoginUser = str(self.ui.autoLogin.currentText())
            if self.ui.createButton.text() == _("Update User"):
                return self.slotCreateUser()
            return True

        if not self.ui.addMoreUsers.isChecked():
            if not self.slotCreateUser():
                ctx.mainScreen.stepIncrement = 0
                return True

        self.refill()
        ctx.installData.autoLoginUser = str(self.ui.autoLogin.currentText())
        return True

    def checkCapsLock(self):
        if pardus.xorg.capslock.isOn():
            self.ui.caps_error.setVisible(True)
        else:
            self.ui.caps_error.setVisible(False)

    def keyReleaseEvent(self, e):
        self.checkCapsLock()

    def showError(self,message):
        self.ui.pass_error.setText("<center>%s</center>" % message)
        self.ui.pass_error.setVisible(True)
        self.ui.createButton.setEnabled(False)

    def slotAdvanced(self):
        self.checkUsers()

    def slotTextChanged(self):
        p1 = self.ui.pass1.text()
        p2 = self.ui.pass2.text()

        if not p1 == '' and (str(p1).lower() == str(self.ui.username.text()).lower() or \
                str(p1).lower() == str(self.ui.realname.text()).lower()):
            self.showError(_('Don\'t use your user name or name as a password.'))
            return
        elif p2 != p1 and p2:
            self.showError(_('Passwords do not match.'))
            return
        elif len(p1) == len(p2) and len(p2) < 4 and not p1=='':
            self.showError(_('Password is too short.'))
            return
        else:
            self.ui.pass_error.setVisible(False)

        if self.ui.username.text() and p1 and p2:
            self.ui.createButton.setEnabled(True)
            if not self.ui.addMoreUsers.isChecked():
                ctx.mainScreen.enableNext()
                ctx.mainScreen.enableBack()
        else:
            self.ui.createButton.setEnabled(False)
            if not self.ui.addMoreUsers.isChecked():
                ctx.mainScreen.disableNext()

    def currentUsers(self):
        ret = []
        for i in range(self.ui.userList.count()):
            ret.append(self.ui.userList.item(i).getUser().username)
        return ret

    def slotUserNameChanged(self):
        self.userNameChanged = True

    def slotRealNameChanged(self):
        if not self.userNameChanged:
            usedUsers = yali.users.getUserList()
            usedUsers.extend(self.currentUsers())
            self.ui.username.setText(yali.users.nickGuess(self.ui.realname.text(), usedUsers))

    def slotCreateUser(self):
        u = yali.users.User()
        u.username = str(self.ui.username.text().toAscii())
        # ignore last character. see bug #887
        u.realname = unicode(self.ui.realname.text())
        u.passwd = unicode(self.ui.pass1.text())
        u.groups = ["users", "pnp", "pnpadmin", "removable", "disk", "audio", "video", "power", "dialout"]
        pix = self.normalUserIcon
        if self.ui.admin.isChecked():
            u.groups.append("wheel")
            pix = self.superUserIcon
        u.noPass = self.ui.noPass.isChecked()

        existsInList = u.username in self.currentUsers()

        # check user validity
        if u.exists() or (existsInList and self.edititemindex == None):
            self.showError(_("This user name is already taken, please choose another one."))
            return False
        elif not u.usernameIsValid():
            # FIXME: Mention about what are the invalid characters!
            self.showError(_("The user name contains invalid characters."))
            return False
        elif not u.realnameIsValid():
            self.showError(_("The real name contains invalid characters."))
            return False

        # Dont check in edit mode
        if self.ui.addMoreUsers.isChecked() and self.ui.userIDCheck.isChecked():
            uid = self.ui.userID.value()
            if self.edititemindex == None:
                if uid in self.usedIDs:
                    self.showError(_('User ID used before, choose another one!'))
                    return False
            self.usedIDs.append(uid)
            u.uid = uid

        self.ui.createButton.setText(_("Add User"))
        self.ui.cancelButton.hide()
        updateItem = None

        try:
            self.ui.userList.takeItem(self.edititemindex)
            self.ui.autoLogin.removeItem(self.edititemindex + 1)
        except:
            updateItem = self.edititemindex
            # nothing wrong. just adding a new user...
            pass

        i = UserItem(self.ui.userList, pix, user = u)

        # add user to auto-login list.
        self.ui.autoLogin.addItem(QString(u.username))

        if updateItem:
            self.ui.autoLogin.setCurrentIndex(self.ui.autoLogin.count())

        # clear form
        self.resetWidgets()

        ctx.debugger.log("slotCreateUser :: user (%s) '%s (%s)' added/updated" % (u.uid, u.realname, u.username))
        ctx.debugger.log("slotCreateUser :: user groups are %s" % str(','.join(u.groups)))

        # give focus to realname widget for a new user. #3280
        self.ui.realname.setFocus()
        self.checkUsers()
        self.userNameChanged = False
        return True

    def slotDeleteUser(self):
        if self.ui.userList.currentRow()==self.edititemindex:
            self.resetWidgets()
            self.ui.autoLogin.setCurrentIndex(0)
        _cur = self.ui.userList.currentRow()
        item = self.ui.userList.item(_cur).getUser()
        if item.uid in self.usedIDs:
            self.usedIDs.remove(item.uid)
        self.ui.userList.takeItem(_cur)
        self.ui.autoLogin.removeItem(_cur + 1)
        self.ui.createButton.setText(_("Add User"))
        self.ui.cancelButton.hide()
        self.checkUsers()

    def slotEditUser(self, item=None):
        if not item:
            item = self.ui.userList.currentItem()
        self.ui.userList.setCurrentItem(item)
        u = item.getUser()
        if u.uid > -1:
            self.ui.userIDCheck.setChecked(True)
            self.ui.userID.setValue(u.uid)
        self.ui.username.setText(QString(u.username))
        self.ui.realname.setText(QString(u.realname))
        self.ui.pass1.setText(QString(u.passwd))
        self.ui.pass2.setText(QString(u.passwd))

        if "wheel" in u.groups:
            self.ui.admin.setChecked(True)
        else:
            self.ui.admin.setChecked(False)

        self.ui.noPass.setChecked(u.noPass)

        self.edititemindex = self.ui.userList.currentRow()
        self.ui.createButton.setText(_("Update User"))
        self.ui.cancelButton.setVisible(self.ui.createButton.isVisible())

    def checkUserFields(self):
        if self.ui.realname.text() and self.ui.username.text() and (str(self.ui.pass1.text()).lower() == str(self.ui.pass2.text()).lower()):
            return True
        else:
            return False

    def checkUsers(self):
        if self.ui.userList.count() > 0:
            self.ui.userList.setCurrentRow(0)
            self.ui.deleteButton.setEnabled(True)
            self.ui.editButton.setEnabled(True)
            self.ui.autoLogin.setEnabled(True)
            ctx.mainScreen.enableNext()
            ctx.mainScreen.enableBack()
            return True
        else:
            if self.checkUserFields():
                ctx.mainScreen.enableNext()
            else:
                ctx.mainScreen.disableNext()

        # there is no user in list so noting to delete
        self.ui.deleteButton.setEnabled(False)
        self.ui.editButton.setEnabled(False)
        self.ui.autoLogin.setEnabled(False)
        return False


    def resetWidgets(self):
        # clear all
        self.edititemindex = None
        self.ui.username.clear()
        self.ui.realname.clear()
        self.ui.pass1.clear()
        self.ui.pass2.clear()
        self.ui.admin.setChecked(False)
        self.ui.noPass.setChecked(False)
        self.ui.userIDCheck.setChecked(False)
        self.ui.createButton.setEnabled(False)
        if self.ui.cancelButton.isVisible():
            self.ui.cancelButton.setHidden(self.sender() == self.ui.cancelButton)
            self.checkUsers()
        self.ui.createButton.setText(_("Add User"))

    def slotReturnPressed(self):
        if self.ui.createButton.isEnabled() and self.ui.addMoreUsers.isChecked():
            self.slotCreateUser()

class UserItem(QtGui.QListWidgetItem):

    ##
    # @param user (yali.users.User)
    def __init__(self, parent, pix, user):
        _pix = QtGui.QIcon(pix)
        _user= QString(user.username)
        QtGui.QListWidgetItem.__init__(self,_pix,_user,parent)
        self._user = user

    def getUser(self):
        return self._user
