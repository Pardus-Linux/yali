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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext



keyboards = {
    0 : {
        "name" : _("Turkish Q"),
        "keymap" : "trq",
        },

    1 : {
        "name" : _("Turkish F"),
        "keymap" : "trf",
        },

    2 : {
        "name" : _("Englis US"),
        "keymap" : "us"
        }
    }


def set_keymap(keymap):
    os.system("setxkbmap -layout %s" % keymap)

def write_keymap(keymap):

    lines = []
    for l in open("/etc/conf.d/keymaps", "r").readlines():
        if l.strip().startswith('KEYMAP='):
            l = 'KEYMAP="%s"\n' % keymap
        lines.append(l)

    open("/etc/conf.d/keymaps", "w").writelines(lines)
