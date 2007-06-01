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

import yali.gui.context as ctx
import GUIStage

##
# Top widget
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        self.img = ctx.iconfactory.newImage("top_image")
        self.label = QLabel(self)
        self.stageWidget = GUIStage.Widget(self)
        
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.label)

        hbox = QHBoxLayout(self._layout)
        hbox.addStretch(1)
        hbox.addWidget(self.stageWidget)
        hbox.addStretch(1)

        
    def slotAddStage(self, obj, text):
        self.stageWidget.slotAddStage(obj, text)


    def setCurrentStage(self, num):
        self.stageWidget.setCurrent(num)


    ##
    # resize the widget (and background image)
    def slotResize(self, obj, size):
        # We change the widget's height regarding the original image
        # to scale properly.
        img_w = self.img.width()
        img_h = self.img.height()
        width = size.width()
        height = img_h * width / img_w
        self.label.setFixedHeight(height)

        # and scale image after all...
        img = self.img.smoothScale(self.label.size())
        self.label.setPaletteBackgroundPixmap(QPixmap(img))
