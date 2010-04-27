# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007, TUBITAK/UEKAE
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

import pisi.ui
import yali4.pisiiface
from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.Ui.checkcdwidget import Ui_CheckCDWidget
import yali4.gui.context as ctx

from yali4.gui.YaliDialog import Dialog

class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Check your media')
    desc = _('To ignore media corruptions you can check your media integrity...')
    icon = "iconCD"
    help = _('''
<font size="+2">Check Packages Integrity!</font>
<font size="+1"><p>
You can check if the packages included in the installation Media are saved correctly. Performing this test is a highly important step in making sure for a problem-free installation. If the test fails, try re-burning the ISO image in a lower (e.g. 12x or less) speed.</p></font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_CheckCDWidget()
        self.ui.setupUi(self)

        self.connect(self.ui.checkButton, SIGNAL("clicked()"),self.slotCheckCD)
        if ctx.consts.lang == "tr":
            self.ui.progressBar.setFormat("%%p")

    def slotCheckCD(self):
        if ctx.yali.checkCDStop == True:
            ctx.yali.checkCDStop = False
            self.ui.checkLabel.setText(_('<font color="#FFF">Please wait while checking Packages.</font>'))
            self.ui.checkButton.setText(_("Stop Checking"))
            # Check the CD
            ctx.yali.checkCD(self.ui)
        else:
            ctx.yali.checkCDStop = True
            self.ui.checkButton.setText(_("Check Packages Integrity"))

