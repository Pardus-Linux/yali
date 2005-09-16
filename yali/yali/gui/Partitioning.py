# -*- coding: utf-8 -*-

from qt import *

from yali.gui.partitionlist import PartitionList
#from yali.gui.parteditwidget import PartEditWidget

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

##
# Edit partition widget
# class PartEdit(PartEditWidget):

#     def __init__(self, *args):
#         apply(PartEdit.__init__, (self,) + args)

#     def setPartition(self, partinfo):
#         pass
