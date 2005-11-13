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

import yali.bootloader
import yali.partitionrequest as request
import yali.partitiontype as parttype
from yali.gui.bootloaderwidget import BootLoaderWidget
from yali.gui.ScreenWidget import ScreenWidget
import yali.gui.context as ctx


##
# BootLoader screen.
class Widget(BootLoaderWidget, ScreenWidget):

    def __init__(self, *args):
        apply(BootLoaderWidget.__init__, (self,) + args)
        

    def execute(self):

        t = parttype.RootPartitionType()
        rootreq = ctx.partrequests.searchPartTypeAndReqType(t,
                                                            request.mountRequestType).next()
        root = basename(rootreq.partition().getPath())
        
        # TODO: use logging!
        yali.bootloader.write_grub_conf(root)
        yali.bootloader.install_files()

        if self.install_bootloader:
            yali.bootloader.install_grub(root)
