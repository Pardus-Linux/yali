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
import shutil
import grp

from yali.constants import consts

# necessary things after a full install


def run_all():
    create_devices()
    initbaselayout()

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


def initbaselayout():
    
    # setup default runlevel symlinks
    # NOT READY!


    def cp(s, d):
        src = os.path.join(consts.target_dir, s)
        dst = os.path.join(consts.target_dir, d)
        shutil.copyfile(src, dst)

    def touch(f, m=0644):
        f = os.path.join(consts.target_dir, f)
        open(f, "w", m).close()

    def chgrp(f, group):
        f = os.path.join(consts.target_dir, f)
        gid = grp.getgrnam(group)
        os.chown(f, 0, gid)

    # create /etc/hosts
    cp("usr/share/baselayout/hosts", "etc/hosts")

    # /etc/passwd, /etc/shadow, /etc/group
    cp("usr/share/baselayout/passwd", "etc/passwd")
    cp("usr/share/baselayout/shadow", "etc/shadow")
    cp("usr/share/baselayout/group", "etc/group")


    # create empty log file
    touch("var/log/lastlog")

    touch("var/run/utmp")
    chgrp("var/run/utmp", "utmp")

    touch("var/log/wtmp")
    chgrp("var/log/wtmp", "utmp")

    
    # depscan -> firstrun
    # modules-update -> firstrun
    # enable shadow groups -> firstrun
