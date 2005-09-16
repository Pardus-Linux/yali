# -*- coding: utf-8 -*-

from qt import *

from yali.gui.partitionlist import PartitionList

##
# Partitioning screen.
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        partlist = PartitionList(self)
        
        hbox = QHBoxLayout(self)
        hbox.addStretch(1)
        hbox.addWidget(partlist)
        hbox.addStretch(1)

