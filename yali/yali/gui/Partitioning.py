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
import yali.parteddata as parteddata

import yali.gui.context as ctx
from yali.gui.GUIException import *
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.partlistwidget import PartListWidget
from yali.gui.parteditbuttons import PartEditButtons
from yali.gui.parteditwidget import PartEditWidget


# partition types in order they are presented in gui.
part_types = {0: parttype.RootPartitionType(),
              1: parttype.HomePartitionType(),
              2: parttype.SwapPartitionType()}

##
# Partitioning screen.
class Widget(QWidget, ScreenWidget):

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

        self.connect(self.partlist, PYSIGNAL("signalSelectionChanged"),
                     self.partedit.slotCancelClicked)

        self.connect(self.partedit, PYSIGNAL("signalApplied"),
                     self.partlist.update)

    def shown(self):
        ctx.screens.prevEnabled()

        self.partlist.update()

    ##
    # do the work and run requested actions on partitions.
    def execute(self):
        # FIXME: check necessities (a root part and a swap?)
        
        for req in ctx.partrequests:
            if req.requestType() == request.formatRequestType:
                req.applyRequest()

        # first mount root (/)
        rootreq = ctx.partrequests.searchPartTypeAndReqType(part_types[0],
                                                            request.mountRequestType).next()
        rootreq.applyRequest()

        for req in ctx.partrequests:
            if req.requestType() == request.mountRequestType and \
                req != rootreq:
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


    def update(self):
        self.list.clear()

        for dev in yali.storage.devices:
            self.addDevice(dev)

        self.createButton.setEnabled(False)
        self.deleteButton.setEnabled(False)
        self.editButton.setEnabled(False)

        self.showPartitionRequests()
        self.checkRootPartRequest()

    def addDevice(self, dev):
        # add the device to the list
        devstr = "%s (%s)" % (dev.getModel(), dev.getName())
        d = PartListItem(self.list, devstr,
                         dev.getSizeStr())
        d.setData(dev)

        # add partitions on device
        for part in dev.getOrderedPartitionList():
            if part.getType() == parteddata.freeSpaceType:
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
        t = item.getData().getType()

        if t == parteddata.deviceType:
            self.createButton.setEnabled(True)
            self.deleteButton.setEnabled(True)
            self.editButton.setEnabled(False)

            self.deleteButton.setText("Delete All Partitions")

        elif t == parteddata.partitionType:
            self.createButton.setEnabled(False)
            self.deleteButton.setEnabled(True)
            self.editButton.setEnabled(True)

            self.deleteButton.setText("Delete Selected Partition")

        elif t == parteddata.freeSpaceType:
            self.createButton.setEnabled(True)
            self.deleteButton.setEnabled(False)
            self.editButton.setEnabled(False)
            

        self.emit(PYSIGNAL("signalSelectionChanged"), ())

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
            if d.getType() == parteddata.partitionType:
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

    def checkRootPartRequest(self):
        ctx.screens.nextDisabled()

        for req in ctx.partrequests:
            if req.partitionType() == part_types[0]:
                # root partition type. can enable next
                ctx.screens.nextEnabled()


##
# Partition List Data stores additional information for partitions.
class PartListItem(QListViewItem):

    # storage.Device or partition.Partition
    _data = None

    def setData(self, d):
        self._data = d

    def getData(self):
        return self._data
        




editState, createState, deleteState = range(3)
  
##
# Edit partition widget
class PartEdit(QWidget):

    _d = None
    _state = None

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
        self._d = d
        self.setState(createState)

    def slotEditPart(self, parent, d):
        self._d = d
        self.setState(editState)

    def slotDeletePart(self, parent, d):
        self._d = d
        self.setState(deleteState)

    ##
    # set up widget for use.
    def setState(self, state):

        # Hacky: show only one widget for an action.
        self.warning.hide()
        self.edit.hide()
        self.show()

        t = self._d.getType()

        if t == parteddata.deviceType:
            if state == createState:
                self.edit.setState(state)
                self.edit.show()

            elif state == deleteState:
                self.warning.setText(
                    "You are going to delete all partitions on device '%s'"
                    %(self._d.getModel()))
                self.warning.show()

        elif t ==  parteddata.partitionType:
            if state == deleteState:
                self.warning.setText(
                    "You are goint to delete partition '%s' on device '%s'!"
                    % (self._d.getMinor(), self._d.getDevice().getModel()))
                self.warning.show()

            elif state == editState:
                self.edit.setState(state, self._d)
                self.edit.show()

        elif t == parteddata.freeSpaceType:
            if state == createState:
                self.edit.setState(state)
                self.edit.show()


        self._state = state


    ##
    # Apply button is clicked, make the necessary modifications and
    # emit a signal.
    def slotApplyClicked(self):
        state = self._state
        t = self._d.getType()

        def check_part_requests():
            i = self.edit.part_type.currentItem()
            t = part_types[i]
            try:
                r = ctx.partrequests.searchPartTypeAndReqType(t,
                                     request.mountRequestType).next()
                self.warning.setText("You have allready have this partition type")
                self.warning.show()
                return False
            except StopIteration:
                # we're O.K.!
                return True


        def create_new_partition(device):
            if not check_part_requests():
                return False

            size = self.edit.size.text().toInt()[0]
                
            # FIXME: set partition type (storage.setPartitionType)
            p = device.addPartition(0, None, size)
            device.commit()
            partition = device.getPartition(p.num)

            if not edit_requests(partition):
                return False

            return True

        def edit_requests(partition):
            if not check_part_requests():
                return False

            edit = self.edit

            i = edit.part_type.currentItem()
            t = part_types[i]

            try:
                ctx.partrequests.append(
                    request.MountRequest(partition, t))
            
                if edit.format.isChecked():
                    ctx.partrequests.append(
                        request.FormatRequest(partition, t))
                else:
                    # remove previous format requests for partition (if
                    # there are any)
                    ctx.partrequests.removeRequest(
                        partition, request.formatRequestType)
            except request.RequestException, e:
                self.warning.setText("%s" % e)
                self.warning.show()
                return False

            return True


        if t == parteddata.deviceType:
            if state == createState:
                device = self._d
                if not create_new_partition(device):
                    return False

            elif state == deleteState:
                self._d.deleteAllPartitions()
                self._d.commit()

        elif t ==  parteddata.partitionType:
            if state == deleteState:
                device = self._d.getDevice()
                device.deletePartition(self._d)
                device.commit()
            elif state == editState:
                partition = self._d
                if not edit_requests(partition):
                    return

        elif t == parteddata.freeSpaceType:
            if state == createState:
                device = self._d.getDevice()
                if not create_new_partition(device):
                    return False

        else:
            raise GUIError, "unknown action called (%s)" %(self._action)


        self.hide()
        self.emit(PYSIGNAL("signalApplied"), ())

    ##
    # Cancel button clicked.
    def slotCancelClicked(self):
        self.hide()


class PartEditWidgetImpl(PartEditWidget):

    def setState(self, state, partition=None):
        self._state = state

        if self._state == editState:
            self.caption.setText("Edit Partition %s" % partition.getMinor())
            self.size.hide()
            self.size_label.hide()

        elif self._state == createState:
            self.caption.setText("Create New Partition")
            self.size.show()
            self.size_label.show()
