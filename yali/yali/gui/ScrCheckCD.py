# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
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


import pisi.ui
import yali.pisiiface
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.checkcdwidget import CheckCDWidget
import yali.gui.context as ctx
from yali.gui.YaliDialog import Dialog

class Widget(CheckCDWidget, ScreenWidget):

    help = _('''
<font size="+2">Check CD Integrity!</font>

<font size="+1">
<p>In this screen, you can check the integrity of the packages in installation CD.
</p>

''')

    def __init__(self, *args):
        apply(CheckCDWidget.__init__, (self,) + args)

        self.pix.setPixmap(ctx.iconfactory.newPixmap("installcd"))

        self.connect(self.checkButton, SIGNAL("clicked()"),
                     self.slotCheckCD)

    def showError(self):
        # make a release notes dialog
        r = ErrorWidget(self)
        d = Dialog(_("Check Failed"), r, self)
        d.resize(300,200)
        d.exec_loop()


    def slotCheckCD(self):
        ctx.screens.disableNext()
        ctx.screens.disablePrev()
        self.checkButton.setEnabled(False)
        self.checkLabel.setText(_('<font color="#FF6D19">Please wait while checking CD.</font>'))
        ctx.screens.processEvents()
        
        yali.pisiiface.initialize(ui=PisiUI())
        yali.pisiiface.add_cd_repo()

        pkg_names = yali.pisiiface.get_available()
        self.progressBar.setTotalSteps(len(pkg_names))
        cur = 0
        for pkg_name in pkg_names:
            cur += 1
            if yali.pisiiface.check_package_hash(pkg_name):
                self.progressBar.setProgress(cur)
            else:
                yali.pisiiface.finalize()
                self.showError()
        yali.pisiiface.finalize() 

        self.checkLabel.setText(_('<font color="#257216">Check succeeded. You can proceed to the next screen.</font>'))
        self.checkLabel.setAlignment(QLabel.SingleLine | QLabel.AlignCenter)
        ctx.screens.enableNext()
        ctx.screens.enablePrev()



class PisiUI(pisi.ui.UI):
    def notify(self, event, **keywords):
        pass
    def display_progress(self, operation, percent, info, **keywords):
	pass

class ErrorWidget(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)

        l = QVBoxLayout(self)
        l.setSpacing(20)
        l.setMargin(10)

        warning = QLabel(self)
        warning.setText(_('''<b>
<p>Integrity check for packages failed. It seems that installation CD is broken.</p>
</b>
'''))

        self.reboot = QPushButton(self)
        self.reboot.setText(_("Reboot"))

        buttons = QHBoxLayout(self)
        buttons.setSpacing(10)
        buttons.addStretch(1)
        buttons.addWidget(self.reboot)

        l.addWidget(warning)
        l.addLayout(buttons)


        yali.sysutils.eject_cdrom()

        self.connect(self.reboot, SIGNAL("clicked()"),
                     self.slotReboot)

    def slotReboot(self):
        self.emit(PYSIGNAL("signalOK"), ())
