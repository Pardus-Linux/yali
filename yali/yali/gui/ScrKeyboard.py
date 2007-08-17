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

import os
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.localedata
import yali.localeutils
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.keyboardwidget import KeyboardWidget
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

        # iterate over keyboard list and set default
        #
        # TODO: re-visit this module and clean this code. there is way
        # to much iteration in here.
        defaultitem = None
        for (lang, keymap) in yali.localedata.getLangsWithKeymaps():
            if isinstance(keymap, list):
                for k in keymap:
                    ki = KeyboardItem(self.keyboard_list, k)
                    if ctx.consts.lang == lang and not defaultitem:
                        defaultitem = ki
            else:
                ki = KeyboardItem(self.keyboard_list, keymap)
                if ctx.consts.lang == lang and not defaultitem:
                    defaultitem = ki

        self.keyboard_list.sort()
        self.keyboard_list.setSelected(defaultitem, True)
        self.slotLayoutChanged(defaultitem)

        self.connect(self.keyboard_list, SIGNAL("selectionChanged(QListBoxItem*)"),
                     self.slotLayoutChanged)

    def shown(self):
        from os.path import basename
        ctx.debugger.log("%s loaded" % basename(__file__))

    def execute(self):
        keydata = self.keyboard_list.selectedItem().getData()
        ctx.installData.keyData = keydata
        return True

    def slotLayoutChanged(self, i):
        keydata = i.getData()
        yali.localeutils.set_keymap(keydata.X)


class KeyboardItem(QListBoxText):

    def __init__(self, parent, keydata):
        text = "%s" %(keydata.translation)
        apply(QListBoxText.__init__, (self,parent,text))
        self._keydata = keydata

    def getData(self):
        return self._keydata
