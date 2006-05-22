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

from os.path import basename
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.storage
import yali.bootloader
import yali.partitionrequest as request
import yali.partitiontype as parttype
from yali.gui.bootloaderwidget import BootLoaderWidget
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.GUIException import *
import yali.gui.context as ctx


##
# BootLoader screen.
class Widget(BootLoaderWidget, ScreenWidget):

    help = _('''
<font size="+2">Boot loader setup</font>

<font size="+1">
<p>
Linux makes use of GRUB boot loader, which
can boot the operating system of your taste
during the start up. 
</p>
<p>
If you have more than one operating system,
you can choose which operating system to 
boot also.
</p>

<p>
Please refer to Pardus Installing and Using 
Guide for more information about GRUB boot 
loader.
</p>
</font>
''')

    def __init__(self, *args):
        apply(BootLoaderWidget.__init__, (self,) + args)
        
        self.device = None


        self.device_list.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.device_list.setPaletteForegroundColor(ctx.consts.fg_color)


        # initialize all storage devices
        if not yali.storage.init_devices():
            raise GUIException, _("Can't find a storage device!")

        if len(yali.storage.devices) > 1:

            # fill device list
            for dev in yali.storage.devices:
                DeviceItem(self.device_list, dev)
            # select the first disk by default
            self.device_list.setSelected(0, True)
            # be sure first is selected device
            self.device = self.device_list.item(0).getDevice()
        else:
            # don't show device list if we have just one disk
            self.device_list.hide()
            self.select_disk_label.hide()
            self.device = yali.storage.devices[0]


        self.connect(self.install_bootloader, SIGNAL("toggled(bool)"),
                     self.slotInstallLoader)
        self.connect(self.device_list, SIGNAL("selectionChanged(QListBoxItem*)"),
                     self.slotDeviceChanged)


    def slotInstallLoader(self, b):
        if b:
            self.device_list.setEnabled(True)
        else:
            self.device_list.setEnabled(False)

    def slotDeviceChanged(self, i):
        self.device = i.getDevice()


    def execute(self):
        loader = yali.bootloader.BootLoader()

        rootreq = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                            request.mountRequestType).next()

        loader.install_dev = basename(self.device.getPath())
        loader.install_root = basename(rootreq.partition().getPath())
        
        # TODO: use logging!
        loader.write_grub_conf()

        # Windows partitions...
        for d in yali.storage.devices:
            for p in d.getPartitions():
                fs = p.getFSName()
                if fs in ("ntfs", "fat32"):
                    loader.win_fs = fs
                    loader.win_dev = basename(p.getDevicePath())
                    loader.win_root = basename(p.getPath())
                    loader.grub_conf_append_win()

        print self.install_bootloader.isChecked()
        if self.install_bootloader.isChecked():
            loader.install_grub()

        return True



class DeviceItem(QListBoxText):

    def __init__(self, parent, dev):
        text = "%s - %s (%s)" %(dev.getModel(),
                                dev.getName(),
                                dev.getSizeStr())
        apply(QListBoxText.__init__, (self,parent,text))
        self._dev = dev
    
    def getDevice(self):
        return self._dev

