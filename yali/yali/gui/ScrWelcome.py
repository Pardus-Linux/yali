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

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.util
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.welcomewidget import Ui_WelcomeWidget
import yali.context as ctx
from yali.gui.YaliDialog import Dialog
from yali.gui.GUIAdditional import Gpl

##
# Welcome screen is the first screen to be shown.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Welcome")
    # FIXME: Use system's pardus release to gather version info and use it if needed
    help = _("""
<font size="+2">Welcome</font>
<font size="+1"><p>Welcome to Pardus that contains many easy-to-use software components. You can do everything you need to, including, but not limited to, connecting to the Internet, creating documents, playing games, listening to music using Pardus.</p>
<p>This application will help you with the installation of Pardus to your computer in few and easy steps and then do what is necessary to identify and configure your hardware. We advise you to backup your data in your disk(s) before starting with the installation.</p>
<p>You can start the installation process (and step in on a free world) by pressing the Next button.</p>
</font>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_WelcomeWidget()
        self.ui.setupUi(self)

        self.connect(self.ui.not_accept, SIGNAL("toggled(bool)"),
                     self.slotNotAcceptToggled)

        self.connect(self.ui.accept, SIGNAL("toggled(bool)"),
                     self.slotAcceptToggled)

        self.connect(self.ui.rebootButton, SIGNAL("clicked()"),
                     self.slotReboot)

        self.connect(self.ui.gplButton, SIGNAL("clicked()"),
                     self.showGPL)

    def slotAcceptToggled(self, b):
        if b:
            self.__enable_next(True)

    def slotNotAcceptToggled(self, b):
        if b:
            self.__enable_next(False)

    def __enable_next(self, b):
        if b:
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def showGPL(self):
        # make a GPL dialog
        d = Dialog("GPL", Gpl(self), self)
        d.resize(500,400)
        d.exec_()

    def slotReboot(self):
        yali.util.eject()
        yali.util.reboot()

    def shown(self):
        ctx.mainScreen.disableBack()
        if self.ui.accept.isChecked():
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()
        ctx.mainScreen.processEvents()

