# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, TUBITAK/UEKAE
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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.localedata
import yali.localeutils
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.networkwidget import NetworkWidget
import yali.gui.context as ctx

##
# Network setup screen
class Widget(NetworkWidget, ScreenWidget):

    help = _('''
<font size="+2">Network Setup</font>

<font size="+1">
<p>
Select the location of the machine
</p>
</font>
''')

    def __init__(self, *args):
        apply(NetworkWidget.__init__, (self,) + args)

        self.mainList.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.mainList.setPaletteForegroundColor(ctx.consts.fg_color)

    def shown(self):
        from os.path import basename
        ctx.debugger.log("%s loaded" % basename(__file__))

    def execute(self):
        return True
