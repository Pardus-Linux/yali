# -*- coding: utf-8 -*-

import os.path
from qt import *

import yali.storage

from yali.gui.partitionlist import PartListWidget
#from yali.gui.parteditwidget import PartEditWidget


##
# Partitioning screen.
class Widget(QWidget):

    _devs = {}

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        devs = yali.storage.detect_all()
        for name in devs:
            d = yali.storage.Device(name)
            d.set_partitions_from_disk()

            name = os.path.basename(name)
            self._devs[name] = d

        self.partlist = PartitionList(self)
#        self.partedit = PartEdit(self)
#        self.partedit.setEnabled(False)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.partlist)
#        vbox.addStretch(1)
#        vbox.addWidget(self.partedit)

        # fill partlist
        for name in self._devs:
            self.partlist.addDevice(self._devs[name])



class PartitionList(PartListWidget):

    def __init__(self, *args):
        apply(PartListWidget.__init__, (self,) + args)

    def addDevice(self, dev):
        name = os.path.basename(dev.get_device())
        devstr = "%s (%s)" % (dev.get_model(), name)

        d = QListViewItem(self.list, devstr)

        for part in dev.get_partitions().itervalues():
            name = "Partition %d" % part.get_minor()
            p = QListViewItem(d, name, part.get_type(), str(part.get_mb()))

        
        self.list.setOpen(d, True)

##
# Edit partition widget
# class PartEdit(PartEditWidget):

#     def __init__(self, *args):
#         apply(PartEdit.__init__, (self,) + args)

#     def setPartition(self, partinfo):
#         pass
