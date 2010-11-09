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

from yali.installdata import installData
from yali.constants import consts
from yali.flags import flags

STEP_DEFAULT, STEP_BASE, STEP_OEM_INSTALL, STEP_FIRST_BOOT, STEP_RESCUE = xrange(5)

STEP_TYPE_STRINGS = {STEP_DEFAULT:"Default",
                     STEP_BASE:"Base System Installation",
                     STEP_OEM_INSTALL:"OEM Installation",
                     STEP_FIRST_BOOT:"First Boot mode",
                     STEP_RESCUE:"System Rescue mode"}

logger = None

storage = None

bootloader = None

interface = None

mainScreen = None

