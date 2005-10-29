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
import yali.partitionrequest as request
import yali.partitiontype as parttype
from yali.parteddata import *

import yali.gui.context as ctx
from yali.gui.GUIException import *
from yali.gui.partlistwidget import PartListWidget
from yali.gui.parteditbuttons import PartEditButtons
from yali.gui.parteditwidget import PartEditWidget


# partition types in order they are presented in gui.
part_types = {0: parttype.RootPartitionType(),
              1: parttype.HomePartitionType(),
              2: parttype.SwapPartitionType()}

##
# Partitioning screen.
class Widget(QWidget):

    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)
        
        # initialize all storage devices
        yali.storage.init_devices()

        self.partlist = PartList(self)
        self.partedit = PartEdit(self)
        self.partedit.hide()

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.partlist)
        vbox.addStretch(1)
        vbox.addWidget(self.partedit)
        
        self.connect(self.partlist, PYSIGNAL("signalCreate"),
                     self.partedit.slotCreatePart)
        self.connect(self.partlist, PYSIGNAL("signalDelete"),
                     self.partedit.slotDeletePart)
        self.connect(self.partlist, PYSIGNAL("signalEdit"),
                     self.partedit.slotEditPart)

        self.connect(self.partedit, PYSIGNAL("signalApplied"),
                     self.partlist.update)

    ##
    # do the work and run requested actions on partitions.
    def execute(self):
        for req in ctx.partrequests:
            req.applyRequest()


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

        self.update()

    def update(self):
        self.list.clear()

        for dev in yali.storage.devices:
            self.addDevice(dev)

        self.createButton.setEnabled(False)
        self.deleteButton.setEnabled(False)
        self.editButton.setEnabled(False)

        self.showPartitionRequests()

    def addDevice(self, dev):
        # add the device to the list
        devstr = "%s (%s)" % (dev.getModel(), dev.getName())
        d = PartListItem(self.list, devstr,
                         dev.getSizeStr())
        d.setData(dev)

        # add partitions on device
        for part in dev.getOrderedPartitionList():
            if part.getFSType() == freespace_fstype:
                name = "Free"
            else:
                name = "Partition %d" % part.getMinor()
            p = PartListItem(d, name,
                             part.getSizeStr(),
                             "", # install partition type
                             part.getFSType())
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
    # iterate over listview and look for a partition
    # @param part: Partition
    # returns: QListViewItem
    def __getItemFromPart(self, part):
        iterator = QListViewItemIterator(self.list)
        current = iterator.current()

        while current:
            d = current.getData()
            if isinstance(d, yali.storage.Partition):
                if d == part:
                     return current
            iterator += 1
            current = iterator.current()

        return None

    ##
    # handle and show requests on listview
    def showPartitionRequests(self):
        for req in ctx.partrequests:
            item = self.__getItemFromPart(req.partition())

            t = req.requestType()
            ptype = req.partitionType()
            if t == request.formatRequestType:
                item.setText(3, ptype.filesystem.name())
                item.setText(4, "YES")

            elif t == request.mountRequestType:
                item.setText(2, ptype.name)


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


    def slotCreatePart(self, parent, d):
        self.setup_iface(d, "create")

    def slotEditPart(self, parent, p):
        self.setup_iface(p, "edit")

    def slotDeletePart(self, parent, d):
        self.setup_iface(d, "delete")

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
                    %(self._d.getModel()))
                self.warning.show()

        elif isinstance(self._d, yali.partition.Partition):
            if act == "delete":
                self._action = "partition_delete"
                self.warning.setText(
                    "You are goint to delete partition '%s' on device '%s'!"
                    % (self._d.getMinor(), self._d.getDevice().getModel()))
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

            self._d.addPartition(0, None, size)
            self._d.commit()
        elif self._action == "device_delete_all_parts":
            self._d.deleteAllPartitions()
            self._d.commit()

        elif self._action == "partition_delete":
            dev = self._d.getDevice()
            dev.deletePartition(self._d)
            dev.commit()
        elif self._action == "partition_edit":
            edit = self.edit

            i = edit.part_type.currentItem()
            t = part_types[i]

            try:
                ctx.partrequests.append(request.MountRequest(self._d, t))
            
                if edit.format.isChecked():
                    ctx.partrequests.append(request.FormatRequest(self._d, t))
                else:
                    # remove previous format requests for partition (if
                    # there are any)
                    ctx.partrequests.removeRequest(self._d,
                                                   request.formatRequestType)
            except request.RequestException, e:
                # FIXME: show this on GUI
                print e

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
            self.caption.setText("Edit Partition %s" % partition.getMinor())
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
