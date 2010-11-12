# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import yali
import yali.context as ctx

class GUIError(yali.Error):
    pass


GUI_STEPS = {ctx.STEP_DEFAULT:("welcome", "mediaCheck", "keyboardSetup",
                           "timeSetup", "accounts", "admin", "driveSelection",
                           "automaticPartitioning", "manualPartitioning", "bootloadersetup",
                           "collectionSelection", "summary", "packageInstallation", "goodbye"),
             ctx.STEP_BASE:("welcome", "mediaCheck", "keyboardSetup",
                        "timeSetup", "driveSelection", "automaticPartitioning",
                        "manualPartitioning", "bootloadersetup", "collectionSelection",
                        "summary", "packageInstallation", "goodbye"),
             ctx.STEP_OEM_INSTALL:("welcome", "mediaCheck", "keyboardSetup", "driveSelection",
                               "automaticPartitioning", "manualPartitioning", "bootloadersetup",
                               "collectionSelection", "summary", "packageInstallation", "goodbye"),
             ctx.STEP_FIRST_BOOT:("welcome", "accounts", "admin", "network", "summary", "goodbye"),
             ctx.STEP_RESCUE:("rescue", "grubRescue", "pisiRescue", "passwordRescue", "finishRescue")}

stepToClass = {"welcome":"ScrWelcome",
               "mediaCheck":"ScrCheckCD",
               "keyboardSetup":"ScrKeyboard",
               "timeSetup":"ScrDateTime",
               "accounts":"ScrUsers",
               "admin":"ScrAdmin",
               "driveSelection":"ScrDriveSelection",
               "automaticPartitioning":"ScrPartitionAuto",
               "manualPartitioning":"ScrPartitionManual",
               "bootloadersetup":"ScrBootloader",
               "collectionSelection":"ScrInstallationAuto",
               "summary":"ScrSummary",
               "packageInstallation":"ScrInstall",
               "goodbye":"ScrGoodbye"}

class ScreenWidget:
    title = ""
    name = ""
    help = ""
    icon = None

    def shown(self):
        pass

    def execute(self):
        return True

    def nextCheck(self):
        return True

    def backCheck(self):
        return True

    def update(self):
        pass
