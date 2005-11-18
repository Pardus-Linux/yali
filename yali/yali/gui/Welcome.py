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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import reboot
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.welcomewidget import WelcomeWidget
import yali.gui.context as ctx

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
This 6-click installation will install Pardus on your hardware,
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
        
        self.rebootButton.hide()
        self.pix.setPixmap(ctx.iconfactory.newPixmap("welcome"))
        

        self.connect(self.not_accept, SIGNAL("toggled(bool)"),
                     self.slotNotAcceptToggled)

        self.connect(self.accept, SIGNAL("toggled(bool)"),
                     self.slotAcceptToggled)

        self.connect(self.rebootButton, SIGNAL("clicked()"),
                     self.slotReboot)


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
        if self.accept.isChecked():
            ctx.screens.nextEnabled()
        else:
            ctx.screens.nextDisabled()

