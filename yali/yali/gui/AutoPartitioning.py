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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.storage
import yali.partitionrequest as request
import yali.partitiontype as parttype
import yali.parteddata as parteddata

from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.autopartwidget import AutoPartWidget
import yali.gui.context as ctx


class Widget(AutoPartWidget, ScreenWidget):

    help = _('''
<font size="+2">Automatic Partitioning</font>

<font size="+1">
<p>
Pardus can be installed on a variety of hardware. You can install Pardus
on an empty disk or hard disk partition. <b>An installation will automatically
destroy the previously saved information on selected partitions. </b>
</p>
<p>
Automatic partitioning use your entire disk for Pardus installation. From 
this screen you can select to automatically partition one of you disks, or
you can skip this screen and try manual partitioning.
</p>
<p>
Please refer to Pardus Installing and Using Guide for more information
about disk partitioning.
</p>
</font>
''')

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

        self.enable_next = False

    def shown(self):
        if self.enable_next:
            ctx.screens.nextEnabled()
        else:
            ctx.screens.nextDisabled()
        ctx.screens.prevEnabled()

    def execute(self):

        def autopartDevice():
            dev = self.device

            # FIXME: also add a swap partition!
            # Or will we?

            # fist delete partitions on device
            dev.deleteAllPartitions()
            dev.commit()

            # FIXME: set partition type (storage.setPartitionType)
            p = dev.addPartition(0, None, dev.getFreeMB())
            p = dev.getPartition(p.num) # get partition.Partition
            dev.commit()

            ctx.partrequests.append(
                request.MountRequest(p, parttype.root))
            ctx.partrequests.append(
                request.FormatRequest(p, parttype.root))


        if self.accept_auto.isChecked():
            ctx.use_autopart = True
            autopartDevice()
            ctx.partrequests.applyAll()

            # skip next screen()
            ctx.screens.next()
        


    def slotDeviceChanged(self, i):
        self.device = i.getDevice()

        if not self.accept_auto.isEnabled():
            self.accept_auto.setEnabled(True)

    def slotButtonsToggled(self, b):
        self.enable_next = True
        ctx.screens.nextEnabled()


class DeviceItem(QListBoxText):

    def __init__(self, parent, dev):
        text = "%s (%s)" %(dev.getModel(), dev.getSizeStr())
        apply(QListBoxText.__init__, (self,parent,text))
        self._dev = dev
    
    def getDevice(self):
        return self._dev

