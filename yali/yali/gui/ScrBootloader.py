# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007, TUBITAK/UEKAE
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
from yali.sysutils import is_windows_boot
from yali.gui.Ui.bootloaderwidget import BootLoaderWidget
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.InformationWindow import InformationWindow
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

        self.device_list.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.device_list.setPaletteForegroundColor(ctx.consts.fg_color)

        self.installFirstMBR.setChecked(True)

        # initialize all storage devices
        if not yali.storage.init_devices():
            raise GUIException, _("Can't find a storage device!")

        if len(yali.storage.devices) > 1:
            self.device_list_state = True
            # fill device list
            for dev in yali.storage.devices:
                DeviceItem(self.device_list, dev)
            # select the first disk by default
            self.device_list.setSelected(0, True)
            # be sure first is selected device
            self.device = self.device_list.item(0).getDevice()
        else:
            # don't show device list if we have just one disk
            self.installMBR.hide()
            self.device_list_state = False
            self.device_list.hide()
            self.select_disk_label.hide()

            self.device = yali.storage.devices[0]

        self.connect(self.buttonGroup, SIGNAL("clicked(int)"),
                     self.slotInstallLoader)
        self.connect(self.device_list, SIGNAL("selectionChanged(QListBoxItem*)"),
                     self.slotDeviceChanged)
        self.connect(self.device_list, SIGNAL("clicked()"),
                     self.slotSelect)

    def shown(self):
        from os.path import basename
        ctx.debugger.log("%s loaded" % basename(__file__))

    def backCheck(self):
        # we need to go partition auto screen, not manual ;)
        num = ctx.screens.getCurrentIndex() - 2
        ctx.screens.goToScreen(num)
        return False

    def slotSelect(self):
        self.installMBR.setChecked(True)

    def slotInstallLoader(self, b):
        if self.installMBR.isChecked():
            self.device_list.setEnabled(True)
            self.device_list.setSelected(0,
                                         True)
        else:
            self.device_list.setEnabled(False)
            self.device_list.setSelected(self.device_list.selectedItem(),
                                         False)

    def slotDeviceChanged(self, i):
        self.device = i.getDevice()

    def execute(self):
        if self.noInstall.isChecked():
            return True

        # show information window...
        # info_window = InformationWindow(self, _("Please wait while installing bootloader!"))

        # loader = yali.bootloader.BootLoader()

        root_part_req = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                                  request.mountRequestType)

        # install_dev

        if self.installPart.isChecked():
            ctx.installData.bootLoaderDev = basename(root_part_req.partition().getPath())
        elif self.installMBR.isChecked():
            ctx.installData.bootLoaderDev = basename(self.device.getPath())
        else:
            ctx.installData.bootLoaderDev = str(filter(lambda u: u.isalpha(),
                                                       basename(root_part_req.partition().getPath())))

        _ins_part = root_part_req.partition().getPath()

        ctx.debugger.log("Pardus installed to : %s" % _ins_part)
        ctx.debugger.log("GRUB will be installed to : %s" % ctx.installData.bootLoaderDev)

        # loader.write_grub_conf(_ins_part,install_dev)

        # Windows partitions...
        #for d in yali.storage.devices:
        #    for p in d.getPartitions():
        #        fs = p.getFSName()
        #        if fs in ("ntfs", "fat32"):
        #            if is_windows_boot(p.getPath(), fs):
        #                win_fs = fs
        #                win_dev = basename(p.getDevicePath())
        #                win_root = basename(p.getPath())
        #                loader.grub_conf_append_win(install_dev,
        #                                            win_dev,
        #                                            win_root,
        #                                            win_fs)
        #                continue

        # finally install it
        # loader.install_grub(install_dev)

        # close window
        # info_window.close(True)

        return True

class DeviceItem(QListBoxText):

    def __init__(self, parent, dev):
        text = u"%s - %s (%s)" %(dev.getModel(),
                                dev.getName(),
                                dev.getSizeStr())
        apply(QListBoxText.__init__, (self,parent,text))
        self._dev = dev

    def getDevice(self):
        return self._dev
