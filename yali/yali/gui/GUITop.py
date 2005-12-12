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

import yali.gui.context as ctx
import GUIStage

##
# Top widget
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        self.img = ctx.iconfactory.newImage("top_image")

        self.stageWidget = GUIStage.Widget(self)

        self._layout = QHBoxLayout(self)
        self._layout.addWidget(self.stageWidget)
        self._layout.addStretch(1)
        
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
        self.setFixedHeight(height)

        # FIXME: calculate a proper margin for widget height
        self._layout.setMargin(height/6)

        # and scale image after all...
        img = self.img.smoothScale(self.size())
        self.setPaletteBackgroundPixmap(QPixmap(img))
