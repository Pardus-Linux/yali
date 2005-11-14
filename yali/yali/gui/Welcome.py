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

from yali.gui.ScreenWidget import ScreenWidget
import yali.gui.context as ctx

##
# Welcome screen is the first screen to be shown.
class Widget(QWidget, ScreenWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        img = QLabel(self)
        img.setPixmap(ctx.iconfactory.newPixmap("welcome"))
        
        hbox = QHBoxLayout(self)
        hbox.addStretch(1)
        hbox.addWidget(img)
        hbox.addStretch(1)

        ctx.screens.prevDisabled()

    def shown(self):
        ctx.screens.prevDisabled()
        ctx.screens.nextEnabled()
