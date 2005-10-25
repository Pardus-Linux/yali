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
from yali.gui.parteditbuttons import PartEditButtons
from yali.gui.parteditwidget import PartEditWidget
from yali.partrequest import *

partition_requests = RequestList()

##
# Partitioning screen.
class Widget(QWidget):

    _devs = {}

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        self.partlist = PartList(self)
        self.partedit = PartEdit(self)
        self.partedit.hide()

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
                     self.slotApplyClicked)
# We don't need to handle this signal now. self.partlist.addDevice
# calls show partition requests.
#        self.connect(self.partedit, PYSIGNAL("signalPartRequest"),
#                     self.partlist.showPartitionRequests)

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

    def slotApplyClicked(self):
        self.partlist.createButton.setEnabled(False)
        self.partlist.deleteButton.setEnabled(False)
        self.partlist.editButton.setEnabled(False)
        
        self.fillPartList()

    def slotCreatePart(self, parent, d):
        self.partedit.setup_iface(d, "create")

    def slotEditPart(self, parent, p):
        self.partedit.setup_iface(p, "edit")

    def slotDeletePart(self, parent, d):
        self.partedit.setup_iface(d, "delete")


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
        self.showPartitionRequests()

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


    def __getItemFromPart(self, part):
        iterator = QListViewItemIterator(self.list)
        current = iterator.current()

        while current:
            d = current.getData()
            if not isinstance(d, yali.storage.Device):
                if d.get_path() == part.get_path():
                     return current
            iterator += 1
            current = iterator.current()

        return None

    ##
    # handle and show requests on listview
    def showPartitionRequests(self):
        for req in partition_requests:
            part = req.get_partition()
            item = self.__getItemFromPart(part)

            if isinstance(req, FormatRequest):
                fs = req.get_fs()
                part_type_name = req.get_part_type_name()
                item.setText(2, part_type_name)
                item.setText(3, fs)
                item.setText(4, "YES")


            elif isinstance(req, MountRequest):
                fs = req.get_fs()
                part_type_name = req.get_part_type_name()
                item.setText(2, part_type_name)
                item.setText(3, fs)



##
# Partition List Data stores additional information for partitions.
class PartListItem(QListViewItem):

    # storage.Device or partition.Partition
    _data = None

    def setData(self, d):
        self._data = d

    def getData(self):
        return self._data
        


##
# Edit partition widget
class PartEdit(QWidget):

    _d = None
    _action = None

    ##
    # Initialize PartEdit
    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        self.vbox = QVBoxLayout(self)

        self.edit = PartEditWidgetImpl(self)
        self.vbox.addWidget(self.edit)

        self.warning = QLabel(self)
        # FIXME: aligning doesn't work!
        self.vbox.addWidget(self.warning, 0, self.vbox.AlignVCenter)

        self.buttons = PartEditButtons(self)
        self.vbox.addWidget(self.buttons)

        self.connect(self.buttons.applyButton, SIGNAL("clicked()"),
                     self.slotApplyClicked)
        self.connect(self.buttons.cancelButton, SIGNAL("clicked()"),
                     self.slotCancelClicked)

    ##
    # set up widget for use.
    def setup_iface(self, d, act):
        self._d = d

        # Hacky: show only one widget for an action.
        self.warning.hide()
        self.edit.hide()
        self.show()


        if isinstance(self._d, yali.storage.Device):
            if act == "create":
                self._action = "device_create"
                self.edit.setState(act)
                self.edit.show()
            elif act == "delete":
                self._action = "device_delete_all_parts"
                self.warning.setText(
                    "You are going to delete all partitions on device '%s'"
                    %(self._d.get_model()))
                self.warning.show()

        elif isinstance(self._d, yali.partition.Partition):
            if act == "delete":
                self._action = "partition_delete"
                self.warning.setText(
                    "Deleting single partition is not implemented yet!")
                self.warning.show()
            if act == "edit":
                self._action = "partition_edit"
                self.edit.setState(act, self._d)
                self.edit.show()



    ##
    # Apply button is clicked, make the necessary modifications and
    # emit a signal.
    def slotApplyClicked(self):

        if self._action == "device_create":
            size = self.edit.size.text().toInt()[0]

            self._d.add_partition(0, None, size)
            self._d.save_partitions()
            self._d.close()
        elif self._action == "device_delete_all_parts":
            self._d.delete_all_partitions()
            self._d.save_partitions()
            self._d.close()

        elif self._action == "partition_delete":
            print "delete_part.."
        elif self._action == "partition_edit":
            edit = self.edit

            part_type = edit.part_type.currentItem()
            partition_requests.append(MountRequest(self._d, part_type))
            
            format = edit.format.isChecked()
            if format:
                partition_requests.append(FormatRequest(self._d, part_type))
            else: #remove previous format requests for partition (if there are any)
                partition_requests.remove_request(self._d, "format")

            # partition requests added signal it for gui to show.
            self.emit(PYSIGNAL("signalPartRequest"), ())

        else:
            raise GUIError, "unknown action called (%s)" %(self._action)

        self.hide()
        self.emit(PYSIGNAL("signalApplied"), ())

    
    ##
    # Cancel button clicked.
    def slotCancelClicked(self):
        self.hide()

  
class PartEditWidgetImpl(PartEditWidget):

    _state = None

    def setState(self, state, partition=None):
        self._state = state

        if self._state == "edit":
            self.caption.setText("Edit Partition %s" % partition.get_minor())
            self.size.hide()

            self.type_label.show()
            self.part_type.show()
            self.format.show()
        elif self._state == "create":
            self.caption.setText("Create New Partition")
            self.type_label.hide()
            self.part_type.hide()
            self.format.hide()

            self.size.show()
