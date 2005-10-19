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
from yali.parteddata import *

from yali.gui.GUIException import *
from yali.gui.partlistwidget import PartListWidget
from yali.gui.parteditwidget import PartEditWidget


##
# Partitioning screen.
class Widget(QWidget):

    _devs = {}

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        self.partlist = PartList(self)
        self.partedit = PartEdit(self)
        self.partedit.setEnabled(False)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.partlist)
        vbox.addStretch(1)
        vbox.addWidget(self.partedit)
        
        self.connect(self.partlist, PYSIGNAL("signalCreate"),
                     self.slotCreatePart)
        self.connect(self.partlist, PYSIGNAL("signalDelete"),
                     self.slotDeletePart)
        self.connect(self.partlist, PYSIGNAL("signalEdit"),
                     self.slotEditPart)

        self.fillPartList()

        self.connect(self.partedit, PYSIGNAL("signalApplied"),
                     self.fillPartList)

    def fillPartList(self):
        
        devs = yali.storage.detect_all()
        for name in devs:
            d = yali.storage.Device(name)
            d.open()

            name = os.path.basename(name)
            self._devs[name] = d

        self.partlist.clear()
        for name in self._devs:
            self.partlist.addDevice(self._devs[name])

    def slotCreatePart(self, parent, d):
        self.partedit.edit(d, "create")

    def slotEditPart(self, parent, p):
        self.partedit.edit(p, "edit")

    def slotDeletePart(self, parent, d):
        self.partedit.edit(d, "delete")

itemTypes = ["device", "partition"]

class PartList(PartListWidget):

    def __init__(self, *args):
        apply(PartListWidget.__init__, (self,) + args)

        # disable sorting
        self.list.setSorting(-1)

        self.connect(self.list, SIGNAL("selectionChanged()"),
                     self.slotItemSelected)
        self.connect(self.createButton, SIGNAL("clicked()"),
                     self.slotCreateClicked)
        self.connect(self.deleteButton, SIGNAL("clicked()"),
                     self.slotDeleteClicked)
        self.connect(self.editButton, SIGNAL("clicked()"),
                     self.slotEditClicked)

    def clear(self):
        self.list.clear()

    def addDevice(self, dev):
        name = os.path.basename(dev.get_device())
        devstr = "%s (%s)" % (dev.get_model(), name)
        total_mb = "%s MB" % dev.get_total_mb()

        d = PartListItem(self.list, devstr, total_mb)
        d.setData(dev)

        for part in dev.get_ordered_partition_list():
            if part.get_fsType() == freespace_fstype:
                name = "Free"
            else:
                name = "Partition %d" % part.get_minor()
            size = "%d MB" % part.get_mb()
            part_type = ""
            fs = part.get_fsType()
            p = PartListItem(d, name, size, part_type, fs)
            p.setData(part)

        
        self.list.setOpen(d, True)

    def slotItemSelected(self):
        item = self.list.currentItem()
        if isinstance(item.getData(), yali.storage.Device):
            self.createButton.setEnabled(True)
            self.deleteButton.setEnabled(True)
            self.editButton.setEnabled(False)

            self.deleteButton.setText("Delete All Partitions")
        else:
            self.createButton.setEnabled(False)
            self.deleteButton.setEnabled(True)
            self.editButton.setEnabled(True)

            self.deleteButton.setText("Delete Selected Partition")

    def slotCreateClicked(self):
        item = self.list.currentItem()
        self.emit(PYSIGNAL("signalCreate"), (self, item.getData()) )

    def slotDeleteClicked(self):
        item = self.list.currentItem()
        self.emit(PYSIGNAL("signalDelete"), (self, item.getData()) )

    def slotEditClicked(self):
        item = self.list.currentItem()
        self.emit(PYSIGNAL("signalEdit"), (self, item.getData()) )


##
# Partition List Data stores additional information for partitions.
class PartListItem(QListViewItem):

    _data = None

    def setData(self, d):
        # device / partition
        self._data = d

    def getData(self):
        return self._data
        


##
# Edit partition widget
class PartEdit(PartEditWidget):

    _d = None
    _action = None

    ##
    # Initialize PartEdit
    def __init__(self, *args):
        apply(PartEditWidget.__init__, (self,) + args)

        self.connect(self.applyButton, SIGNAL("clicked()"),
                     self.slotApplyClicked)

    ##
    # edit partition/ create partition on device
    def edit(self, d, act):
        self.setEnabled(True)
        self._d = d
        self._action = act


    ##
    # Apply button is clicked, make the necessary modifications and
    # emit a signal.
    def slotApplyClicked(self):
        size = self.size.text().toInt()[0]

        if isinstance(self._d, yali.storage.Device):
            if self._action == "create":
                self._d.add_partition(0, None, size)
                self._d.save_partitions()
                self._d.close()
            elif self._action == "delete":
                self._d.delete_all_partitions()
                self._d.save_partitions()
                self._d.close()
        else:
            print "edit partition, resize, fstype or mount point change..."

        self.setEnabled(False)
        self.emit(PYSIGNAL("signalApplied"), ())
