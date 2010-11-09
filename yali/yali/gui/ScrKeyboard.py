# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, SIGNAL, QVariant

import yali.localeutils
import yali.localedata
import yali.context as ctx
from yali.gui import ScreenWidget, register_gui_screen
from yali.gui.Ui.keyboardwidget import Ui_KeyboardWidget

##
# Keyboard setup screen
class Widget(QWidget, ScreenWidget):
    name = "keyboardSetup"
    title = _("Choose a Keyboard Layout")
    icon = "input-keyboard"
    help = _("""A keyboard layout is a description of how keys are placed on a keyboard. There are different keyboard layouts in use throughout the world. The one you will want to use, generally depends on the country you live in or the language you use.
This screen lets you select the keyboard layout you want to use on Pardus. You can test the selected layout by typing something in the given textbox.
""")

    def __init__(self):
        QWidget.__init__(self, None)
        self.ui = Ui_KeyboardWidget()
        self.ui.setupUi(self)

        index = 0 # comboBox.addItem doesn't increase the currentIndex
        self.default_layout_index = None
        for country, data in yali.localedata.locales.items():
            if data["xkbvariant"]:
                i = 0
                for variant in data["xkbvariant"]:
                    _d = dict(data)
                    _d["xkbvariant"] = variant[0]
                    _d["name"] = variant[1]
                    _d["consolekeymap"] = data["consolekeymap"][i]
                    self.ui.keyboard_list.addItem(_d["name"], QVariant(data))
                    i += 1
            else:
                self.ui.keyboard_list.addItem(data["name"], QVariant(data))
            if ctx.consts.lang == country:
                if ctx.consts.lang == "tr":
                    self.default_layout_index = index + 1
                else:
                    self.default_layout_index = index
            index += 1


        self.ui.keyboard_list.setCurrentIndex(self.default_layout_index)
        self.slotLayoutChanged()

        self.connect(self.ui.keyboard_list, SIGNAL("currentIndexChanged(int)"),
                self.slotLayoutChanged)

    def slotLayoutChanged(self):
        index = self.ui.keyboard_list.currentIndex()
        keymap = self.ui.keyboard_list.itemData(index).toMap()
        # Gökmen's converter
        keymap = dict(map(lambda x: (str(x[0]), unicode(x[1].toString())), keymap.iteritems()))
        ctx.installData.keyData = keymap
        yali.localeutils.setKeymap(keymap["xkblayout"], keymap["xkbvariant"])

    def execute(self):
        ctx.logger.debug("Selected keymap is : %s" % ctx.installData.keyData["name"] )
        return True

register_gui_screen(Widget)
