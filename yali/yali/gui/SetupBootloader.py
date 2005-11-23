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
        

    def execute(self):

        rootreq = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                            request.mountRequestType).next()
        root = basename(rootreq.partition().getPath())
        dev = basename(rootreq.partition().getDevicePath())
        
        # TODO: use logging!
        yali.bootloader.write_grub_conf(root, dev)
        yali.bootloader.install_files()

        # Windows partitions...
        for d in yali.storage.devices:
            for p in d.getPartitions():
                fs = p.getFSType()
                if fs in ("ntfs", "fat32"):
                    dev = basename(p.getDevicePath())
                    root = basename(p.getPath())
                    yali.bootloader.grub_conf_append_win(root, dev, fs)

        print self.install_bootloader.isChecked()
        if self.install_bootloader.isChecked():
            print "installing"
            yali.bootloader.install_grub(root, dev)
