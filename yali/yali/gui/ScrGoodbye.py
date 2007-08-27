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

import os
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import comar
import time
import yali.sysutils
import yali.users
import yali.localeutils
import yali.postinstall
import yali.bootloader
import yali.storage
import yali.partitionrequest as partrequest
import yali.partitiontype as parttype
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.YaliDialog import WarningDialog
from yali.constants import consts
import yali.gui.context as ctx

##
# Goodbye screen
class Widget(QWidget, ScreenWidget):

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
        apply(QWidget.__init__, (self,) + args)
        
        img = QLabel(self)
        img.setPixmap(ctx.iconfactory.newPixmap("goodbye"))

        self.info = QLabel(self)
        self.info.setText(
            _('<b><font size="+2" color="#FF6D19">Rebooting system. Please wait!</font></b>'))
        self.info.hide()
        self.info.setAlignment(QLabel.AlignCenter|QLabel.AlignTop)
        self.info.setMinimumSize(QSize(0,50))

        vbox = QVBoxLayout(self)
        vbox.addStretch(1)

        hbox = QHBoxLayout(vbox)
        hbox.addStretch(1)
        hbox.addWidget(img)
        hbox.addStretch(1)

        vbox.addStretch(1)
        vbox.addWidget(self.info)

    def shown(self):
        from os.path import basename
        ctx.debugger.log("%s loaded" % basename(__file__))
        ctx.screens.disablePrev()
        self.processPendingActions()
        self.installBootloader()

    def execute(self):
        ctx.screens.disableNext()

        self.info.show()
        self.info.setAlignment(QLabel.AlignCenter)

        try:
            ctx.debugger.log("Trying to umount %s" % (ctx.consts.target_dir + "/home"))
            yali.sysutils.umount(ctx.consts.target_dir + "/home")
            ctx.debugger.log("Trying to umount %s" % (ctx.consts.target_dir))
            yali.sysutils.umount(ctx.consts.target_dir)
        except:
            ctx.debugger.log("Umount Failed.")
            pass

        ctx.debugger.log("Trying to eject the CD.")
        # remove cd...
        w = RebootWidget(self)
        ctx.debugger.log("Show reboot dialog.")
        self.dialog = WarningDialog(w, self)
        self.dialog.exec_loop()

        ctx.debugger.log("Yali, fastreboot calling..")

        # store log content
        if ctx.debugEnabled:
            open(ctx.consts.log_file,"w").write(str(ctx.debugger.traceback.plainLogs))

        yali.sysutils.fastreboot()

    # process pending actions defined in other screens.
    def processPendingActions(self):
        for i in range(20):
            try:
                ctx.debugger.log("trying to start comar..")
                link = comar.Link(sockname=consts.comar_socket_file)
                break
            except comar.CannotConnect:
                time.sleep(1)
                ctx.debugger.log("wait comar for 1 second...")

        link.Net.Stack.setHostNames(hostnames=ctx.installData.hostName)
        reply = link.read_cmd()
        ctx.debugger.log("Hostname set as %s" % ctx.installData.hostName)

        # add users
        for u in yali.users.pending_users:
            ctx.debugger.log("User %s adding to system" % u.username)
            link.User.Manager.addUser(name=u.username,
                                      password=u.passwd,
                                      realname=u.realname,
                                      groups=','.join(u.groups))
            ctx.debugger.log("RESULT :: %s" % str(link.read_cmd()))

            # Enable auto-login
            if u.username == ctx.installData.autoLoginUser:
                u.setAutoLogin()

        link.User.Manager.setUser(uid=0,
                                  password=ctx.installData.rootPassword)
        ctx.debugger.log("RESULT :: %s" % str(link.read_cmd()))

        # write console keyboard data
        yali.localeutils.write_keymap(ctx.installData.keyData.console)
        ctx.debugger.log("Keymap stored.")

        # migrate xorg.conf
        yali.postinstall.migrate_xorg_conf(ctx.installData.keyData.X)
        ctx.debugger.log("xorg.conf merged.")

    def installBootloader(self):
        ctx.debugger.log("Bootloader is installing...")
        loader = yali.bootloader.BootLoader()
        root_part_req = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                                  partrequest.mountRequestType)
        _ins_part = root_part_req.partition().getPath()
        loader.write_grub_conf(_ins_part,ctx.installData.bootLoaderDev)

        # Check for windows partitions.
        for d in yali.storage.devices:
            for p in d.getPartitions():
                fs = p.getFSName()
                if fs in ("ntfs", "fat32"):
                    if is_windows_boot(p.getPath(), fs):
                        win_fs = fs
                        win_dev = basename(p.getDevicePath())
                        win_root = basename(p.getPath())
                        loader.grub_conf_append_win(ctx.installData.bootLoaderDev,
                                                    win_dev,
                                                    win_root,
                                                    win_fs)
                        continue

        # finally install it
        loader.install_grub(ctx.installData.bootLoaderDev)
        ctx.debugger.log("Bootloader installed.")

class RebootWidget(QWidget):

    def __init__(self, *args):
        QWidget.__init__(self, *args)

        l = QVBoxLayout(self)
        l.setSpacing(20)
        l.setMargin(10)

        warning = QLabel(self)
        warning.setText(_('''<b>
<p>Please remove Pardus CD from your drive and pres Reboot button.</p>
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
