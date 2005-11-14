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

import os

from yali.constants import consts

# necessary things after a full install


def create_devices():

    target = os.path.join(consts.target_dir, "dev/null")
    if not os.path.exists(target):
        os.popen("mknod --mode=666 %s c 1 3" % target)

    target = os.path.join(consts.target_dir, "dev/console")
    if not os.path.exists(target):
        os.popen("mknod %s c 5 1" % target)

    target = os.path.join(consts.target_dir, "dev/null")
    if not os.path.exists(target):
        os.popen("mknod %s c 4 1" % target)



