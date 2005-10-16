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


import os.path
from qt import *

import yali.storage

from yali.gui.partlistwidget import PartListWidget
from yali.gui.parteditwidget import PartEditWidget


##
# Partitioning screen.
class Widget(QWidget):

    _devs = {}

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        devs = yali.storage.detect_all()
        for name in devs:
            d = yali.storage.Device(name)
            d.open()

            name = os.path.basename(name)
            self._devs[name] = d

        self.partlist = PartList(self)
        self.partedit = PartEdit(self)
        self.partedit.setEnabled(False)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.partlist)
        vbox.addStretch(1)
        vbox.addWidget(self.partedit)

        # fill partlist
        for name in self._devs:
            self.partlist.addDevice(self._devs[name])



class PartList(PartListWidget):

    def __init__(self, *args):
        apply(PartListWidget.__init__, (self,) + args)

    def addDevice(self, dev):
        name = os.path.basename(dev.get_device())
        devstr = "%s (%s)" % (dev.get_model(), name)
        total_mb = "%s MB" % dev.get_total_mb()

        d = PartListItem(self.list, devstr, total_mb)

        for part in dev.get_partitions().itervalues():
            name = "Partition %d" % part.get_minor()
            size = "%d MB" % part.get_mb()
            part_type = ""
            fs = part.get_fsType()
            p = PartListItem(d, name, size, part_type, fs)

        
        self.list.setOpen(d, True)


##
# Partition List Data stores additional information for partitions.
class PartListItem(QListViewItem):

    _type = None

    def setType(self, t):
        # device / partition
        self._type = t
        


##
# Edit partition widget
class PartEdit(PartEditWidget):

    def __init__(self, *args):
        apply(PartEditWidget.__init__, (self,) + args)

    def setPartition(self, partinfo):
         pass
