# -*- coding: utf-8 -*-

from qt import *

import GUIStage

##
# Top widget
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        self.img = QImage("pics/top_image.png")

        self.stageWidget = GUIStage.Widget(self)

        self._layout = QHBoxLayout(self)
        self._layout.addStretch(1)
        self._layout.addWidget(self.stageWidget)
        
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
