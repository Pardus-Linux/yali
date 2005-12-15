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
import yali.partitionrequest as request
import yali.partitiontype as parttype
from yali.gui.YaliDialog import Dialog
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.PartListImpl import PartList
from yali.gui.PartEditImpl import PartEdit, \
    editState, createState, deleteState, resizeState


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
swap space (between 500 MB - 2 GB, according to your needs) for 
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
        self.dialog = None

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.partlist)
        
        self.connect(self.partlist, PYSIGNAL("signalCreate"),
                     self.slotCreatePart)

        self.connect(self.partlist, PYSIGNAL("signalDelete"),
                     self.slotDeletePart)

        self.connect(self.partlist, PYSIGNAL("signalEdit"),
                     self.slotEditPart)

        self.connect(self.partlist, PYSIGNAL("signalResize"),
                     self.slotResizePart)


        self.connect(self.partedit, PYSIGNAL("signalApplied"),
                     self.slotApplied)

        self.connect(self.partedit, PYSIGNAL("signalCanceled"),
                     self.slotCanceled)


    def shown(self):
        ctx.screens.enablePrev()

        self.partlist.update()

    ##
    # do the work and run requested actions on partitions.
    def execute(self):

        # inform user...
        self.partlist.showPartitionRequests(formatting=True)
        # process events and show partitioning information!
        ctx.screens.processEvents()

        
        ##
        # check swap partition, if not present use swap file
        rt = request.mountRequestType
        pt = parttype.swap
        found_swap_part = [x for x in ctx.partrequests.searchPartTypeAndReqType(pt, rt)]
        # this should give (at most) one result
        # cause we are storing one request for a partitionType()
        assert(len(found_swap_part) <= 1)


        if not found_swap_part:
            print "no swap partition defined using swap as file..."
            # find root partition
            for r in ctx.partrequests.searchReqType(request.mountRequestType):
                ctx.partrequests.append(
                    request.SwapFileRequest(r.partition(), r.partitionType()))

        # apply all partition requests
        ctx.partrequests.applyAll()


    def slotCreatePart(self, parent, d):
        self.partedit.setState(createState, d)
        self.dialog = Dialog(_("Create Partition"), self.partedit, self)
        self.dialog.exec_loop()

    def slotDeletePart(self, parent, d):
        self.partedit.setState(deleteState, d)
        self.dialog = Dialog(_("Delete Partition"), self.partedit, self)
        self.dialog.exec_loop()

    def slotEditPart(self, parent, d):
        self.partedit.setState(editState, d)
        self.dialog = Dialog(_("Edit Partition"), self.partedit, self)
        self.dialog.exec_loop()

    def slotResizePart(self, parent, d):
        self.partedit.setState(resizeState, d)
        self.dialog = Dialog(_("Resize Partition"), self.partedit, self)
        self.dialog.exec_loop()


    def slotApplied(self):
        self.dialog.done(0)
        del self.dialog
        self.partlist.update()

    def slotCanceled(self):
        self.dialog.reject()
        del self.dialog
