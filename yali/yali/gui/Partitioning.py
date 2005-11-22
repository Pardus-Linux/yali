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

import yali.gui.context as ctx
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.PartListImpl import PartList
from yali.gui.PartEditImpl import PartEdit


##
# Partitioning screen.
class Widget(QWidget, ScreenWidget):

    help = _('''
<font size="+2">Partitioning your hard disk</font>

<font size="+1">
<p>
Pardus can be installed on a variety of hardware. You can install Pardus
on an empty disk or hard disk partition. <b>An installation will automatically
destroy the previously saved information on selected partitions. </b>
</p>
<p>
In order to use Pardus, you must create one Linux filesystem (for the 
basic files and folders) and a swap space (for improved performance). 
We advise you to allocate at least 4 GBs of hard disk area and 
swap space (between 500 Mb - 2 GB, according to your needs) for 
convenience. A Linux partition size less than 2.5 GB is not allowed.
</p>
<p>
Please refer to Pardus Installing and Using Guide for more information
about disk partitioning.
</p>
</font>
''')


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

        # inform user...
        self.partlist.showPartitionRequests(formatting=True)
        # process events and show partitioning information!
        ctx.screens.processEvents()

        # apply all partition requests
        ctx.partrequests.applyAll()
