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
from yali.gui.YaliDialog import Dialog
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.PartListImpl import PartList
from yali.gui.PartEditImpl import PartEdit, \
    editState, createState, deleteState


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
 

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.partlist)
        
        self.connect(self.partlist, PYSIGNAL("signalCreate"),
                     self.slotCreatePart)

        self.connect(self.partlist, PYSIGNAL("signalDelete"),
                     self.slotDeletePart)

        self.connect(self.partlist, PYSIGNAL("signalEdit"),
                     self.slotEditPart)


#        self.connect(self.partedit, PYSIGNAL("signalApplied"),
#                     self.partlist.update)

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


    def slotCreatePart(self, parent, d):
        partedit = PartEdit(self)
        partedit.setState(createState, d)
        d = Dialog(_("Create Partition"), partedit, self)
        d.exec_loop()

    def slotDeletePart(self, parent, d):
        partedit = PartEdit(self)
        partedit.setState(deleteState, d)
        d = Dialog(_("Delete Partition"), partedit, self)
        d.exec_loop()

    def slotEditPart(self, parent, d):
        partedit = PartEdit(self)
        partedit.setState(editState, d)
        d = Dialog(_("Edit Partition"), partedit, self)
        d.exec_loop()
