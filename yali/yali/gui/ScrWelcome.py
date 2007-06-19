# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007, TUBITAK/UEKAE
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

import yali.sysutils
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.welcomewidget import WelcomeWidget
import yali.gui.context as ctx
from yali.gui.YaliDialog import Dialog
import GUIGPL

##
# Welcome screen is the first screen to be shown.
class Widget(WelcomeWidget, ScreenWidget):

    help = _('''
<font size="+2">Welcome!</font>

<font size="+1">
<p>Welcome to Pardus, your new and practical desktop with a handful 
of applications tailored to your needs. With Pardus, you can 
connect to internet, read your e-mails online, work with 
documents, listen to music and play DVDs. Its advanced yet
easy interface will let you be more productive and efficient.
</p>

<p>
This software will install Pardus on your computer,
without disrupting your previous documents and settings. However,
we advise you to make a backup before proceeding. 
</p>
<p>
The installer will identify your system's hardware and configure
it according to your needs. You will note the arrow keys on the
bottom of the screen: Use them to advance to next screen.
</p>
<p>
Have a fruitful experience with Pardus!
</p>
</font>
''')

    def __init__(self, *args):
        apply(WelcomeWidget.__init__, (self,) + args)
        self.rebootButton.setEnabled(False)
        self.pix.setPixmap(ctx.iconfactory.newPixmap("welcome"))
        

        self.connect(self.not_accept, SIGNAL("toggled(bool)"),
                     self.slotNotAcceptToggled)

        self.connect(self.accept, SIGNAL("toggled(bool)"),
                     self.slotAcceptToggled)

        self.connect(self.rebootButton, SIGNAL("clicked()"),
                     self.slotReboot)

        self.connect(self.gplButton, SIGNAL("clicked()"),
                     self.showGPL)


    def slotAcceptToggled(self, b):
        if b:
            self.__enable_next(True)

    def slotNotAcceptToggled(self, b):
        if b:
            self.__enable_next(False)
    
    def __enable_next(self, b):
        if b:
            ctx.screens.enableNext()
            self.rebootButton.setEnabled(False)
        else:
            ctx.screens.disableNext()
            self.rebootButton.setEnabled(True)


    def showGPL(self):
        # make a release notes dialog
        r = GUIGPL.Widget(self)
        d = Dialog("GPL", r, self)
        d.resize(500,400)
        d.exec_loop()



    def slotReboot(self):
        yali.sysutils.fastreboot()




    def shown(self):
        ctx.screens.disablePrev()
        if self.accept.isChecked():
            ctx.screens.enableNext()
        else:
            ctx.screens.disableNext()
