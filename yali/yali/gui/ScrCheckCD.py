# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2010 TUBITAK/UEKAE
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

import pisi.ui
import yali.pisiiface
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.checkcdwidget import Ui_CheckCDWidget
import yali.context as ctx

from yali.gui.YaliDialog import Dialog

class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Check the Integrity of Packages")
    icon = "media-optical-small"
    help = _("""Here you can validate the integrity of the installation packages. A failed validation usually is a sign of a badly mastered installation medium (CD, DVD or USB storage).
If you are using an optical installation medium, try burning the installation image using DAO (Disc-at-once) mode, at a lower speed (4x for DVD, 8-12x for CD).
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_CheckCDWidget()
        self.ui.setupUi(self)

        self.ui.validationSucceedBox.hide()
        self.ui.validationFailBox.hide()
        self.ui.progressBar.hide()

        self.connect(self.ui.checkButton, SIGNAL("clicked()"),self.slotCheckCD)
        if ctx.consts.lang == "tr":
            self.ui.progressBar.setFormat("%%p")

    def slotCheckCD(self):
        if ctx.yali.checkCDStop == True:
            ctx.yali.checkCDStop = False
            self.ui.progressBar.show()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/gui/pics/dialog-error.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.checkButton.setIcon(icon)
            self.ui.checkButton.setText("")
            ctx.yali.checkCD(self.ui)
        else:
            ctx.yali.checkCDStop = True
            self.ui.progressBar.show()
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/gui/pics/task-accepted.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.checkButton.setIcon(icon)
            self.ui.checkButton.setText(_("Validate"))
