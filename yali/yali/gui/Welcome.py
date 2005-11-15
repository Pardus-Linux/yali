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

import reboot
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.welcomewidget import WelcomeWidget
import yali.gui.context as ctx

##
# Welcome screen is the first screen to be shown.
class Widget(WelcomeWidget, ScreenWidget):

    def __init__(self, *args):
        apply(WelcomeWidget.__init__, (self,) + args)
        
        self.rebootButton.hide()
        self.pix.setPixmap(ctx.iconfactory.newPixmap("welcome"))
        

        self.connect(self.not_accept, SIGNAL("toggled(bool)"),
                     self.slotNotAcceptToggled)

        self.connect(self.accept, SIGNAL("toggled(bool)"),
                     self.slotAcceptToggled)

        self.connect(self.rebootButton, SIGNAL("clicked()"),
                     self.slotReboot)

        ctx.screens.prevDisabled()
        ctx.screens.nextDisabled()


    def slotAcceptToggled(self, b):
        if b:
            self.__enable_next(True)

    def slotNotAcceptToggled(self, b):
        if b:
            self.__enable_next(False)
    
    def __enable_next(self, b):
        if b:
            ctx.screens.nextEnabled()
            self.rebootButton.hide()
        else:
            ctx.screens.nextDisabled()
            self.rebootButton.show()

    def slotReboot(self):
        reboot.fastreboot()

    def shown(self):
        ctx.screens.prevDisabled()
        ctx.screens.nextEnabled()

