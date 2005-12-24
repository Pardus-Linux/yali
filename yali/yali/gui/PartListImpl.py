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


import time
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.storage
import yali.filesystem as filesystem
import yali.partitionrequest as request
import yali.partitiontype as parttype
import yali.parteddata as parteddata

import yali.gui.context as ctx
from yali.gui.partlistwidget import PartListWidget



class PartList(PartListWidget):

    def __init__(self, *args):
        apply(PartListWidget.__init__, (self,) + args)

        self.list.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.list.setPaletteForegroundColor(ctx.consts.fg_color)


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
        self.connect(self.resizeButton, SIGNAL("clicked()"),
                     self.slotResizeClicked)

        self.connect(self.resetButton, SIGNAL("clicked()"),
                     self.resetChanges)

        self.connect(self.list, SIGNAL("doubleClicked(QListViewItem*, const QPoint&, int)"),
                     self.slotListDoubleClicked)

    def update(self):
        self.list.clear()

        for dev in yali.storage.devices:
            self.addDevice(dev)

        self.createButton.setEnabled(False)
        self.deleteButton.setEnabled(False)
        self.editButton.setEnabled(False)

        self.showPartitionRequests()
        self.checkRootPartRequest()

    def resetChanges(self):
        yali.storage.clear_devices()
        yali.storage.init_devices()
        self.update()


    def devices_commit(self):
        for dev in yali.storage.devices:
            dev.commit()

        # wait for udev to create device nodes
        time.sleep(2)

    def addDevice(self, dev):

        def sizeStr(mb):
            if mb > 1024:
                return _("%0.1f GB free") % long(mb/1024.0)
            else:
                return _("%d MB free") % mb

        # add the device to the list
        devstr = "%s (%s)" % (dev.getModel(), dev.getName())
        freespace = dev.getFreeMB()
        if freespace:
            size_str = dev.getSizeStr() + "  (%s)" % sizeStr(freespace)
        else:
            size_str = dev.getSizeStr()

        d = PartListItem(self.list, devstr,
                         size_str)
        d.setData(dev)


        # than add extended partition to reparent logical ones
        if dev.hasExtendedPartition():
            ext = dev.getExtendedPartition()
            free_ext = ext.getFreeMB()
            if free_ext:
                size_str = ext.getSizeStr() + "  (%s)" % sizeStr(free_ext)
            else:
                size_str = ext.getSizeStr()

            e = PartListItem(d,
                             _("Extended"),
                             size_str)
            e.setData(ext)

#
# Don't show free space as a new item on GUI #
#
#            freespace = ext.getFreeMB()
#            if freespace:
#                f = PartListItem(e,
#                                 _("Free"),
#                                 str(freespace))
#                # freespace's data is extended partition. we'll use it later on...
#                f.setData(ext)


        # add partitions on device
        for part in dev.getOrderedPartitionList():
            parent_item = d

            if part.isExtended():
                continue

            elif part.getType() == parteddata.freeSpaceType:
                # Don't show free space as a new item on GUI #
                #name = _("Free")
                continue

            else:
                name = _("Partition %d") % part.getMinor()
                if part.isLogical():
                    parent_item = e

            p = PartListItem(parent_item,
                             name,
                             part.getSizeStr(),
                             "", # install partition type
                             part.getFSName())
            p.setData(part)

        self.list.setOpen(d, True)
        try:
            self.list.setOpen(e, True)
        except:
            # no extended partition...
            pass

    def slotItemSelected(self):
        item = self.list.currentItem()
        d = item.getData()
        t = d.getType()

        if t == parteddata.deviceType:
            if d.getFreeMB() > 0 and d.primaryAvailable():
                self.createButton.setEnabled(True)
            else:
                self.createButton.setEnabled(False)
            self.deleteButton.setEnabled(True)
            self.resizeButton.setEnabled(False)
            self.editButton.setEnabled(False)

            self.deleteButton.setText(_("Delete All Partitions"))

        elif t == parteddata.partitionType:

            # check if partition is resizeable
            fs = filesystem.get_filesystem(d.getFSName())            
            resizeable = False
            if fs:
                if fs.isResizeable():
                    resizeable = True
            self.resizeButton.setEnabled(resizeable)


            if d.isExtended():
                if d.getFreeMB() > 0:
                    self.createButton.setEnabled(True)
            else:
                self.createButton.setEnabled(False)


            self.deleteButton.setEnabled(True)


            if not d.isExtended(): # don't edit extended partititons
                self.editButton.setEnabled(True)

            self.deleteButton.setText(_("Delete Selected Partition"))

        elif t == parteddata.freeSpaceType:
            if d.getDevice().primaryAvailable():
                self.createButton.setEnabled(True)
            self.deleteButton.setEnabled(False)
            self.resizeButton.setEnabled(False)
            self.editButton.setEnabled(False)
            

        self.emit(PYSIGNAL("signalSelectionChanged"), ())

    def slotCreateClicked(self):
        item = self.list.currentItem()
        self.emit(PYSIGNAL("signalCreate"), (self, item.getData()) )

    def slotDeleteClicked(self):
        item = self.list.currentItem()
        self.emit(PYSIGNAL("signalDelete"), (self, item.getData()) )

    def slotResizeClicked(self):
        item = self.list.currentItem()
        self.emit(PYSIGNAL("signalResize"), (self, item.getData()) )

    def slotEditClicked(self):
        item = self.list.currentItem()
        self.emit(PYSIGNAL("signalEdit"), (self, item.getData()) )


    def slotListDoubleClicked(self, item, point, c):
        t = item.getData().getType()

        if t == parteddata.partitionType:
            self.slotEditClicked()


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
    def showPartitionRequests(self, formatting=False):
        for req in ctx.partrequests:
            item = self.__getItemFromPart(req.partition())

            t = req.requestType()
            ptype = req.partitionType()
            if t == request.formatRequestType:
                item.setText(3, ptype.filesystem.name())
                if formatting:
                    item.setText(4, _("Formatting!"))
                else:
                    item.setText(4, _("YES"))

            elif t == request.mountRequestType:
                item.setText(2, ptype.name)


    def checkRootPartRequest(self):
        ctx.screens.disableNext()

        for req in ctx.partrequests:
            if req.partitionType() == parttype.root:
                # root partition type. can enable next
                ctx.screens.enableNext()


##
# Partition List Data stores additional information for partitions.
class PartListItem(QListViewItem):

    # storage.Device or partition.Partition
    _data = None

    def setData(self, d):
        self._data = d

    def getData(self):
        return self._data
        

