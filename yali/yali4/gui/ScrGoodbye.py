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

import os

import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import dbus
import time
import yali4.sysutils
import yali4.users
import yali4.localeutils
import yali4.postinstall
import yali4.bootloader
import yali4.storage
import yali4.partitionrequest as partrequest
import yali4.partitiontype as parttype
from os.path import basename
from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.YaliDialog import InfoDialog
from yali4.gui.YaliSteps import YaliSteps
from yali4.gui.Ui.goodbyewidget import Ui_GoodByeWidget
import yali4.gui.context as ctx
from yali4.gui.installdata import *

##
# Goodbye screen
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Goodbye from YALI')
    desc = _('Enjoy your fresh Pardus !...')
    help = _('''
<font size="+2">Congratulations</font>


<font size="+1">
<p>
You have successfully installed Pardus, a very easy to use desktop system on
your machine. Now you can start playing with your system and stay productive
all the time.
</p>
<P>
Click on the Next button to proceed. One note: You remember your password,
don't you?
</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_GoodByeWidget()
        self.ui.setupUi(self)

        self.steps = YaliSteps()

    def shown(self):
        ctx.mainScreen.disableNext()
        ctx.yali.info.updateAndShow(_("Running post install operations.."))
        ctx.mainScreen.disableBack()
        ctx.yali.processPendingActions(self)
        self.steps.slotRunOperations()
        if not ctx.mainScreen.ui.helpContent.isVisible():
            ctx.mainScreen.slotToggleHelp()
        self.ui.label.setPixmap(QtGui.QPixmap(":/gui/pics/goodbye.png"))
        ctx.yali.info.hide()
        ctx.mainScreen.enableNext()

    def execute(self):
        ctx.mainScreen.disableNext()

        ctx.debugger.log("Show reboot dialog.")
        InfoDialog(_("Press <b>Reboot</b> button to restart your system."), _("Reboot"))

        ctx.yali.info.updateAndShow(_('<b>Rebooting system. Please wait!</b>'))

        # remove cd...
        if not ctx.yali.install_type == YALI_FIRSTBOOT:
            ctx.debugger.log("Trying to eject the CD.")
            yali4.sysutils.ejectCdrom()

        ctx.debugger.log("Yali, reboot calling..")

        ctx.mainScreen.processEvents()
        time.sleep(4)
        yali4.sysutils.reboot()

