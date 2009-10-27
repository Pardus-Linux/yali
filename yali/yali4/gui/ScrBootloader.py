# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#


import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import time
import thread
from os.path import basename

import yali4.storage
from yali4.gui.installdata import *
from yali4.gui.GUIAdditional import DeviceItem
from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.Ui.bootloaderwidget import Ui_BootLoaderWidget
from yali4.gui.GUIException import *
import yali4.gui.context as ctx


##
# BootLoader screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Bootloader Choice')
    desc = _('Configure the system boot...')
    icon = "iconBootloader"
    help = _('''
<font size="+2">Boot loader setup</font>
<font size="+1">
<p>
Pardus 2009 uses a boot manager called GRUB to start the operating system you choose.
</p>
<p>If there are multiple operating systems in your computer, you can start the one 
you like using GRUB. Installing GRUB to the beginning of the boot disk is the advised 
option to avoid boot problems.  If you are sure you know what you are doing, 
you can change boot loader settings.
</p>
<p>
Please refer to Pardus Installing and Using 
Guide for more information about GRUB boot 
loader.
</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_BootLoaderWidget()
        self.ui.setupUi(self)

        self.ui.installFirstMBR.setChecked(True)

        # initialize all storage devices
        if not yali4.storage.initDevices():
            raise GUIException, _("Can't find a storage device!")

        # fill device list
        for dev in yali4.storage.devices:
            DeviceItem(self.ui.device_list, dev)
        # select the first disk by default
        self.ui.device_list.setCurrentRow(0)
        # be sure first is selected device
        self.device = self.ui.device_list.item(0).getDevice()

        if len(yali4.storage.devices) < 1:
            # don't show device list if we have just one disk
            self.ui.installMBR.hide()
            self.ui.device_list.hide()

            self.device = yali4.storage.devices[0]

        self.connect(self.ui.device_list, SIGNAL("currentItemChanged(QListWidgetItem*,QListWidgetItem*)"),
                     self.slotDeviceChanged)
        self.connect(self.ui.installFirstMBR, SIGNAL("clicked()"),
                     self.slotDisableList)
        self.connect(self.ui.installPart, SIGNAL("clicked()"),
                     self.slotDisableList)
        self.connect(self.ui.noInstall, SIGNAL("clicked()"),
                     self.slotDisableList)
        self.connect(self.ui.installMBR, SIGNAL("clicked()"),
                     self.slotEnableList)
        self.connect(self.ui.device_list, SIGNAL("itemClicked(QListWidgetItem*)"),
                     self.slotSelect)

    def shown(self):
        yali4.storage.setOrderedDiskList()
        ctx.debugger.log("Disks BIOS Boot order : %s " % ','.join(ctx.installData.orderedDiskList))
        self.getBootable().setBootable()

    def getBootable(self):
        for i in range(self.ui.device_list.count()):
            item = self.ui.device_list.item(i)
            if item.getDevice().getPath() == ctx.installData.orderedDiskList[0]:
                return item

    def backCheck(self):
        if ctx.autoInstall:
            # we need to go partition auto screen, not manual ;)
            ctx.mainScreen.moveInc = 2
        return True

    def slotDisableList(self):
        self.ui.device_list.setEnabled(False)
        self.ui.device_list.setCurrentItem(self.getBootable())

    def slotEnableList(self):
        self.ui.device_list.setEnabled(True)

    def slotSelect(self):
        self.ui.installMBR.toggle()

    def slotDeviceChanged(self, o, n):
        self.device = o.getDevice()
        ctx.bootLoaderOptionalDev = self.device

    def execute(self):
        ctx.installData.bootLoaderOptionalDev = self.device
        # Apply GRUB Options
        if self.ui.noInstall.isChecked():
            ctx.installData.bootLoaderOption = B_DONT_INSTALL
        elif self.ui.installPart.isChecked():
            ctx.installData.bootLoaderOption = B_INSTALL_PART
        elif self.ui.installMBR.isChecked():
            ctx.installData.bootLoaderOption = B_INSTALL_MBR
        else:
            ctx.installData.bootLoaderOption = B_INSTALL_SMART
        ctx.installData.bootLoaderDetectOthers = self.ui.autoAddOthers.isChecked()
        return True

