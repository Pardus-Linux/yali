# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui

import time
import yali.postinstall
import yali.pisiiface
from yali import sysutils
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.YaliDialog import InfoDialog
from yali.gui.YaliSteps import YaliSteps
from yali.gui.Ui.goodbyewidget import Ui_GoodByeWidget
import yali.gui.context as ctx
from yali.gui.installdata import *

##
# Goodbye screen
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Rescue Mode')
    desc = _('Final step of Rescue operations...')
    help = _('''
<font size="+2">Rescue Mode</font>
<font size="+1"><p>Click <b>next</b> to reboot !</p></font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_GoodByeWidget()
        self.ui.setupUi(self)

        self.steps = YaliSteps()

    def installBootLoader(self):
        # Install bootloader
        ctx.yali.installBootloader(ctx.installData.rescuePartition)
        return True

    def takeBackPisi(self):
        try:
            yali.pisiiface.takeBack(ctx.takeBackOperation.no)
        except Exception, e:
            ctx.debugger.log("Exception occured while taking back !!")
            ctx.debugger.log(e)
            return False
        return True

    def shown(self):
        ctx.mainScreen.disableNext()
        if ctx.rescueMode == "grub":
            self.steps.setOperations([{"text":      _("Installing BootLoader..."),
                                       "operation": self.installBootLoader}])
        elif ctx.rescueMode == "pisi":
            self.steps.setOperations([{"text":      _("Taking back Pisi operation..."),
                                       "operation": self.takeBackPisi}])

        ctx.yali.info.updateAndShow(_("Running rescue operations.."))
        ctx.mainScreen.disableBack()
        self.steps.slotRunOperations()

        # Umount system paths
        yali.sysutils.umountSystemPaths()

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
            sysutils.ejectCdrom()

        ctx.debugger.log("Yali, reboot calling..")

        ctx.mainScreen.processEvents()
        sysutils.run("sync")
        time.sleep(4)
        sysutils.reboot()

