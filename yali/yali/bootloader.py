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

from os import system
from os.path import join

from yali.constants import const

grub_conf_tmp = """
default 0
timeout 5
splashimage = %(grub_root)s/boot/grub/splash.xpm.gz

title=2.6.12-2 [ %(pardus_version)s ]
root %(grub_root)s
kernel %(grub_root)s/boot/pardus-kernel-2.6.12-2 ro root=%(root)s

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

    grub_conf_file = join(constants.target_dir, "boot/grub/grub.conf")

    grub_conf = grub_conf_tmp % {"root": root,
                                 "grub_root": get_grub_style(root)
                                 "pardus_version": consts.pardus_version}

    open(grub_conf_file, "w").write(grub_conf)


def install_grub(root):

    grub_shell = grub_shell_tmp % {"grub_root": get_grub_style(root)}

    open("/tmp/grub-shell", "w").write(grub_shell)

    system("grub-install --grub-shell=/tmp/grub-shell")
