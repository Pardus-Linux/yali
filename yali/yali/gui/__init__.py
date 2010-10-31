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
import os
import yali
import yali.context as ctx

class GUIError(yali.Error):
    pass

STEP_DEFAULT, STEP_BASE, STEP_OEM_INSTALL, STEP_FIRST_BOOT, STEP_RESCUE = xrange(5)

STEP_TYPE_STRINGS = {STEP_DEFAULT:"Default",
                     STEP_BASE:"Base System Installation",
                     STEP_OEM_INSTALL:"OEM Installation",
                     STEP_FIRST_BOOT:"First Boot mode",
                     STEP_RESCUE:"System Rescue mode"}

GUI_STEPS = {STEP_DEFAULT:("kahya", "welcome", "mediaCheck", "keyboardSetup",
                           "timeSetup", "accounts", "admin", "driveSelection",
                           "automaticPartitioning", "manualPartitioning", "bootloadersetup",
                           "collectionSelection", "summary", "packageInstallation", "goodbye"),
             STEP_BASE:("welcome", "mediaCheck", "keyboardSetup",
                        "timeSetup", "driveSelection", "automaticPartitioning",
                        "manualPartitioning", "bootloadersetup", "collectionSelection",
                        "summary", "packageInstallation", "goodbye"),
             STEP_OEM_INSTALL:("welcome", "mediaCheck", "keyboardSetup", "driveSelection",
                               "automaticPartitioning", "manualPartitioning", "bootloadersetup",
                               "collectionSelection", "summary", "packageInstallation", "goodbye"),
             STEP_FIRST_BOOT:("welcome", "keyboardSetup", "timeSetup", "accounts", "admin", "goodbye"),
             STEP_RESCUE:("rescue", "grubRescue", "pisiRescue", "passwordRescue", "finishRescue")}

GUI_SCREENS = {}

def register_gui_screen(screen):
    if not issubclass(screen, ScreenWidget):
        raise ValueError("arg1 must be a subclass of ScreenWidget")

    GUI_SCREENS[screen.type] = screen
    ctx.logger.debug("registered screen type %s" % screen.type)

def collect_screens():
    """ Pick up all device screen classes from this directory.

        Note: Modules must call register_device_screen(ScreenWidget) in
              order for the screen class to be picked up.
    """
    dir = os.path.dirname(__file__)
    for moduleFile in os.listdir(dir):
        if moduleFile.startswith("Scr") and \
        moduleFile.endswith(".py") and \
        moduleFile != __file__:
            print "moduleFile:%s" % moduleFile
            module_name = moduleFile[:-3]
            try:
                print "%s is importing" % module_name
                globals()[module_name] = __import__(module_name, globals(), locals(), [], -1)
            except ImportError:
                ctx.logger.debug("import of screen module '%s' failed %s" % module_name)
            except Exception, msg:
                print "%s is importing patladi:\n %s" % (module_name, msg)


def get_screens(install_type):
    screens = []
    for step in GUI_STEPS[install_type]:
        screens.append(GUI_SCREENS[step])
    return screens

class ScreenWidget:
    title = ""
    type = ""
    desc = ""
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

collect_screens()
