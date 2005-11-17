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


from qt import *

import yali.storage
import yali.partitionrequest as request
import yali.partitiontype as parttype
import yali.parteddata as parteddata

from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.autopartwidget import AutoPartWidget
import yali.gui.context as ctx


class Widget(AutoPartWidget, ScreenWidget):

    def __init__(self, *args):
        apply(AutoPartWidget.__init__, (self,) + args)
        
        self.device = None
        
        # initialize all storage devices
        yali.storage.init_devices()

        # fill device list
        for dev in yali.storage.devices:
            DeviceItem(self.device_list, dev)

        # don't enable auto partitioning if no device is selected
        self.accept_auto.setEnabled(False)

        self.connect(self.accept_auto, SIGNAL("toggled(bool)"),
                     self.slotButtonsToggled)
        self.connect(self.manual, SIGNAL("toggled(bool)"),
                     self.slotButtonsToggled)

        self.connect(self.device_list, SIGNAL("selectionChanged(QListBoxItem*)"),
                     self.slotDeviceChanged)


    def shown(self):
        if not self.accept_auto.isEnabled():
            ctx.screens.nextDisabled()
        ctx.screens.prevEnabled()

    def execute(self):

        def autopartDevice():
            dev = self.device

            # FIXME: also add a swap partition!
            # Or will we?

            t = parttype.RootPartitionType()

            # fist delete partitions on device
            dev.deleteAllPartitions()
            dev.commit()

            # FIXME: set partition type (storage.setPartitionType)
            p = dev.addPartition(0, None, dev.getFreeMB())
            p = dev.getPartition(p.num) # get partition.Partition
            dev.commit()

            ctx.partrequests.append(
                request.MountRequest(p, t))
            ctx.partrequests.append(
                request.FormatRequest(p, t))

        def applyRequests():
            for req in ctx.partrequests:
                if req.requestType() == request.formatRequestType:
                    req.applyRequest()

            for req in ctx.partrequests:
                if req.requestType() == request.mountRequestType:
                    req.applyRequest()


        if self.accept_auto.isChecked():
            ctx.use_autopart = True
            autopartDevice()
            applyRequests()

            # skip next screen()
            ctx.screens.next()
        


    def slotDeviceChanged(self, i):
        self.device = i.getDevice()

        if not self.accept_auto.isEnabled():
            self.accept_auto.setEnabled(True)

    def slotButtonsToggled(self, b):
        ctx.screens.nextEnabled()


class DeviceItem(QListBoxText):

    def __init__(self, parent, dev):
        text = "%s (%s)" %(dev.getModel(), dev.getSizeStr())
        apply(QListBoxText.__init__, (self,parent,text))
        self._dev = dev
    
    def getDevice(self):
        return self._dev

