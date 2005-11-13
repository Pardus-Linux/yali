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

grub_conf_tmp = """
default 0
timeout 5
splashimage = (%(grub_root)s)/boot/grub/splash.xpm.gz

title=2.6.12-2 [ %(pardus_version)s ]
root (%(grub_root)s)
kernel (%(grub_root)s)/boot/pardus-kernel-2.6.12-2 ro root=%(root)s

"""

grub_shell_tmp = """
root %(grub_root)
setup (hd0)
"""


def get_grub_style(d):
    h = {}
    for i in range(4):
        h[chr(97+i)] = str(i)
    p = d[0:2]
    p = p + h.get(d[2])
    p = p + "," + str(int(d[3]) - 1)
    return p


def write_grub_conf(root):

    d = os.path.join(consts.target_dir, "boot/grub")
    grub_conf_file = os.path.join(d, "grub.conf")

    if not os.path.exists(d):
        os.makedirs(d)

    grub_conf = grub_conf_tmp % {"root": root,
                                 "grub_root": get_grub_style(root),
                                 "pardus_version": consts.pardus_version}

    open(grub_conf_file, "w").write(grub_conf)


def install_files():
    src = os.path.join(consts.target_dir, "lib/grub")
    src2 = os.path.join(consts.target_dir, "usr/lib/grub")
    fnlist = glob.glob(src + "/*/*")
    fnlist2 = glob.glob(src2 + "/*/*")
    for x in fnlist2: fnlist.append(x)

    for x in fnlist:
        if os.path.isfile(x):
            fname = os.path.basename(x)
            newpath = os.path.join(consts.target_dir, "boot/grub", fname)
            shutil.copyfile(x, newpath)


def install_grub(root):

    d = os.path.join(consts.target_dir, "boot/grub/device.map")
    c = os.path.join(consts.target_dir, "boot/grub/grub.conf")
    cmd = "/sbin/grub --batch --device-map=%s < %s > /dev/null 2>&1" %(d,c)
    os.system(cmd)

    grub_shell = grub_shell_tmp % {"grub_root": get_grub_style(root)}

    open("/tmp/grub-shell", "w").write(grub_shell)

    # FIXME: check command...
    os.system("grub-install --grub-shell=/tmp/grub-shell")
