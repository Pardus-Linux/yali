# -*- coding: utf-8 -*-

from qt import *

##
# Welcome screen is the first screen to be shown.
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        img = QLabel(self)
        img.setPixmap(QPixmap("pics/welcome.png"))
        
        hbox = QHBoxLayout(self)
        hbox.addStretch(1)
        hbox.addWidget(img)
        hbox.addStretch(1)

