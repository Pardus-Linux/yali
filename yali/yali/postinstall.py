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


def initbaselayout():
    
    def cp(s, d):
        src = os.path.join(consts.target_dir, s)
        dst = os.path.join(consts.target_dir, d)
        shutil.copyfile(src, dst)

    def touch(f, m=0644):
        f = os.path.join(consts.target_dir, f)
        open(f, "w", m).close()

    def chgrp(f, group):
        f = os.path.join(consts.target_dir, f)
        gid = int(grp.getgrnam(group)[2])
        os.chown(f, 0, gid)

    # create /etc/hosts
    cp("usr/share/baselayout/hosts", "etc/hosts")

    # create /etc/ld.so.conf
    cp("usr/share/baselayout/ld.so.conf", "etc/ld.so.conf")

    # /etc/passwd, /etc/shadow, /etc/group
    cp("usr/share/baselayout/passwd", "etc/passwd")
    cp("usr/share/baselayout/shadow", "etc/shadow")
    os.chmod(os.path.join(consts.target_dir, "etc/shadow"), 0600)
    cp("usr/share/baselayout/group", "etc/group")


    # create empty log file
    touch("var/log/lastlog")

    touch("var/run/utmp", 0664)
    chgrp("var/run/utmp", "utmp")

    touch("var/log/wtmp", 0664)
    chgrp("var/log/wtmp", "utmp")

    # create needed device nodes
    os.system("/usr/bin/mknod %s/dev/console c 5 1" % consts.target_dir)
    os.system("/usr/bin/mknod %s/dev/null c 1 3" % consts.target_dir)


    # workaround for #4069. remove after Beta2
    if not os.path.exists("/root"):
        os.mkdir("/root")
    for x in os.listdir("/etc/skel"):
        src = os.path.join("/etc/skel", x)
        dst = os.path.join("/root", x)
        if os.path.exists(dst):
            continue
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
    os.chown("/root", 0, 0)
    os.chmod("/root", 0700)
    # end workaround


def migrate_xorg_conf(keymap="trq"):
    # copy xorg.conf.
    src = "/etc/X11/xorg.conf"
    if os.path.exists(src):
        dst = open(os.path.join(consts.target_dir, "etc/X11/xorg.conf"), "w")
        for l in open(src, "r"):
            if l.find("XkbLayout") != -1:
                l = '    Option    "XkbLayout" "%s"\n' %(keymap)
            dst.write(l)
        dst.close()

