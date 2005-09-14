# -*- coding: utf-8 -*-

from qt import *

##
# Partitioning screen.
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        img = QLabel(self)
        img.setText("SetupUsers: Not implemented yet!")
        
        hbox = QHBoxLayout(self)
        hbox.addStretch(1)
        hbox.addWidget(img)
        hbox.addStretch(1)

