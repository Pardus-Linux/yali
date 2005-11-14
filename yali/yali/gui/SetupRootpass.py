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
from yali.gui.rootpasswidget import RootPassWidget
import yali.gui.context as ctx

##
# Root password widget
class Widget(RootPassWidget, ScreenWidget):

    def __init__(self, *args):
        apply(RootPassWidget.__init__, (self,) + args)
        
        self.pass_error.hide()

        self.connect(self.pass1, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)
        self.connect(self.pass2, SIGNAL("textChanged(const QString &)"),
                     self.slotTextChanged)

    def shown(self):
        ctx.screens.prevDisabled()

        # TODO: check password
        ctx.screens.nextEnabled()

    def execute(self):
        pass
        # write password to system...

    def slotTextChanged(self):
        
        p1 = self.pass1.text()
        p2 = self.pass2.text()

        if p2 != p1:
            self.pass_error.show()
            # TODO: disable next button!
        else:
            self.pass_error.hide()

        self.pass_error.setAlignment(QLabel.AlignCenter)
