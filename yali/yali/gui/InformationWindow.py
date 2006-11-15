# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from qt import *
import yali.gui.context as ctx

class InformationWindow(QMainWindow):

    def __init__(self, parent, text):
        QMainWindow.__init__(self, parent, "infowin", Qt.WStyle_NoBorder)

        l = QHBoxLayout(self)
        frame = QFrame(self)
        frame.setPaletteBackgroundColor(ctx.consts.border_color)
        frame.setFrameStyle(frame.PopupPanel|frame.Plain)
        l.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setMargin(2)
        label = QLabel(frame)
        label.setText(text)
        label.setAlignment(QLabel.SingleLine | QLabel.AlignCenter)
        layout.addWidget(label)
        
        fm = QFontMetrics(label.font())
        self.resize(fm.width(text) + 20,
                    fm.height() + 10)

        self.move(parent.width()/2 - self.width()/2,
                  parent.height()/2 - self.height()/2)
        self.show()
