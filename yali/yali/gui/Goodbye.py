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


import os
from qt import *

import yali.sysutils
from yali.gui.ScreenWidget import ScreenWidget
import yali.gui.context as ctx

##
# Goodbye screen
class Widget(QWidget, ScreenWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        img = QLabel(self)
        img.setPixmap(ctx.iconfactory.newPixmap("goodbye"))

        self.info = QLabel(self)
        self.info.setText(
            '<b><font size="+2" color="red">Rebooting system. Please wait!</font></b>')
        self.info.hide()
        self.info.setAlignment(QLabel.AlignCenter)


        vbox = QVBoxLayout(self)
        vbox.addStretch(1)

        hbox = QHBoxLayout(vbox)
        hbox.addStretch(1)
        hbox.addWidget(img)
        hbox.addStretch(1)

        vbox.addStretch(1)
        vbox.addWidget(self.info)


    def execute(self):

        ctx.screens.nextDisable()
        ctx.screens.prevDisable()

        self.info.show()
        self.info.setAlignment(QLabel.AlignCenter)

        cmd = yali.sysutils.find_executable("reboot")
        os.system(cmd)
