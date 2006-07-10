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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.keyboard
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.keyboardwidget import KeyboardWidget
import yali.gui.context as ctx

##
# Keyboard setup screen
class Widget(KeyboardWidget, ScreenWidget):

    help = _('''
<font size="+2">Keyboard Setup</font>

<font size="+1">
<p>
Depending on your hardware or choice select a keyboard layout from the list.
</p>
</font>
''')

    def __init__(self, *args):
        apply(KeyboardWidget.__init__, (self,) + args)
        
        self.pix.setPixmap(ctx.iconfactory.newPixmap("keyboards"))

        self.keyboard_list.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.keyboard_list.setPaletteForegroundColor(ctx.consts.fg_color)

        f = self.keyboard_list.font()
        f.setBold(True)
        self.keyboard_list.setFont(f)


        for k in yali.keyboard.keyboards:
            KeyboardItem(self.keyboard_list, yali.keyboard.keyboards[k])

        self.keyboard_list.setSelected(0, True)
        # use first item...
        self.slotLayoutChanged(self.keyboard_list.item(0))


        self.connect(self.keyboard_list, SIGNAL("selectionChanged(QListBoxItem*)"),
                     self.slotLayoutChanged)


    def shown(self):
        ctx.screens.enablePrev()
        ctx.screens.enableNext()

    def execute(self):
        keydata = self.keyboard_list.selectedItem().getData()

        ctx.keydata = keydata

        return True

    def slotLayoutChanged(self, i):
        keydata = i.getData()
        yali.keyboard.set_keymap(keydata["keymap"])


class KeyboardItem(QListBoxText):

    def __init__(self, parent, keydata):
        text = "%s" %(keydata["name"])
        apply(QListBoxText.__init__, (self,parent,text))
        self._keydata = keydata
    
    def getData(self):
        return self._keydata
