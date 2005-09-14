# -*- coding: utf-8 -*-

from qt import *

##
# Welcome screen is the first screen to be shown.
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        img = QLabel(self)
        img.setPixmap(QPixmap("pics/welcome.png"))
        

        top = QHBoxLayout(self)
        top.setMargin(10)
        top.addStretch(1)
        top.addWidget(img)

#    def paintEvent(self, e):
        # FIXME: We should also change the widget's height regarding
        # the original image to scale properly.
        # DON'T use paintEvet. Instead grab the resized signal from YaliWindow
#        img = self.img.smoothScale(self.size())
#        self.setPaletteBackgroundPixmap(QPixmap(img))
