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
import sys
import string
import pardus.xorg
import gettext

_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, SIGNAL, QLineEdit

import yali.util
import yali.postinstall
import yali.context as ctx
from yali.gui import ScreenWidget, register_gui_screen
from yali.gui.Ui.rootpasswidget import Ui_RootPassWidget

##
# Root password widget
class Widget(QWidget, ScreenWidget):
    name = "admin"
    title = _("Choose an Administrator Password and a Hostname")
    icon = "iconAdmin"
    help = _("""
<p>
You need to define a password for the "root" user which is the conventional name
of the user who has all rights and permissions (to all files and programs) in all
modes (single or multi-user).
</p>

<p>
Your password must be easy to remember but strong enough to resist possible attacks.
You can use capital and lower-case letters, numbers and punctuation marks in your password.
</p>

<p>
You can also define a hostname for your computer. A hostname is an identifier assigned to your computer. As your computer will be recognized with this name in the local network, it is recommended to select a descriptive hostname.
</p>
""")

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_RootPassWidget()
        self.ui.setupUi(self)
        self.intf = ctx.interface

        self.host_valid = True
        self.pass_valid = False

        self.connect(self.ui.pass1, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.pass2, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.ui.pass2, SIGNAL("returnPressed()"),
                     self.slotReturnPressed)
        self.connect(self.ui.hostname, SIGNAL("textChanged(const QString &)"),
                     self.slotHostnameChanged)

    def update(self):
        if self.host_valid and self.pass_valid:
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def shown(self):
        if ctx.installData.hostName:
            self.ui.hostname.setText(str(ctx.installData.hostName))
        else:
            # Use first added user's name as machine name if its exists
            release_hostname = yali.util.product_release()
            if self.ui.hostname.text() == '':
                self.ui.hostname.setText(release_hostname)

        if ctx.installData.rootPassword:
            self.ui.pass1.setText(ctx.installData.rootPassword)
            self.ui.pass2.setText(ctx.installData.rootPassword)

        self.update()
        self.checkCapsLock()
        self.ui.pass1.setFocus()

    def execute(self):
        ctx.installData.rootPassword = unicode(self.ui.pass1.text())
        ctx.installData.hostName = unicode(self.ui.hostname.text())

        if ctx.flags.install_type == ctx.STEP_DEFAULT:
            #FIXME:Refactor dirty code
            if ctx.storageInitialized:
                disks = filter(lambda d: not d.format.hidden, ctx.storage.disks)
                if len(disks) == 1:
                    ctx.storage.clearPartDisks = [disks[0].name]
                    ctx.mainScreen.step_increment = 2
                else:
                    ctx.mainScreen.step_increment = 1
            else:
                ctx.storageInitialized = yali.storage.initialize(ctx.storage, ctx.interface)
                if not ctx.storageInitialized:
                    return False
                else:
                    disks = filter(lambda d: not d.format.hidden, ctx.storage.disks)
                    if len(disks) == 1:
                        ctx.storage.clearPartDisks = [disks[0].name]
                        ctx.mainScreen.step_increment = 2
                    else:
                        ctx.mainScreen.step_increment = 1

        return True

    def setCapsLockIcon(self, child):
        if type(child) == QLineEdit:
            if pardus.xorg.capslock.isOn():
                child.setStyleSheet("QLineEdit {background: url(:/gui/pics/caps.png) no-repeat right;\npadding-right: 35px}")
            else:
                child.setStyleSheet("QLineEdit {background: none; padding-right: 0px}")

    def checkCapsLock(self):
        for child in self.ui.groupBox.children():
            self.setCapsLockIcon(child)

    def keyReleaseEvent(self, event):
        self.checkCapsLock()

    def slotTextChanged(self):

        password = str(self.ui.pass1.text())
        password_confirm = str(self.ui.pass2.text())

        if password and password == password_confirm:
            if len(password) < 4:
                self.intf.informationWindow.update(_('Password is too short.'), type="error")
                self.pass_valid = False
            elif filter(lambda x: not x in string.ascii_letters, password):
                self.intf.informationWindow.update(_("Don't use invalid characters"), type="error")
            else:
                self.intf.informationWindow.hide()
                self.pass_valid = True
        else:
            self.pass_valid = False
            if password_confirm:
                self.intf.informationWindow.update(_('Passwords do not match.'), type="error")

        if password.lower()=="root" or password_confirm.lower()=="root":
            self.pass_valid = False
            if password_confirm:
                self.intf.informationWindow.update(_('Do not use your username as your password.'), type="error")

        if self.pass_valid:
            self.intf.informationWindow.hide()

        self.update()

    def slotHostnameChanged(self, hostname):
        if len(hostname) > 64:
            self.host_valid = False
            self.intf.informationWindow.update(_('Hostname cannot be longer than 64 characters.'), type="error")
            self.update()
            return


        if not hostname.toAscii():
            self.host_valid = False
            self.update()
            return

        self.host_valid = yali.util.is_text_valid(hostname.toAscii())

        if not self.host_valid:
            self.intf.informationWindow.update(_('Hostname contains invalid characters.'), type="error")
        else:
            self.intf.informationWindow.hide()
        self.update()


    def slotReturnPressed(self):
        if ctx.mainScreen.isNextEnabled():
            ctx.mainScreen.slotNext()


register_gui_screen(Widget)
