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

from yali.constants import consts


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
        "name" : _("English US"),
        "keymap" : "us"
        },

    3 : {
        "name" : _("Dutch"),
        "keymap" : "nl"
        },

    4 : {
	"name" : _("German"),
	"keymap" : "de"
	}
    }


def set_keymap(keymap):
    os.system("setxkbmap -layout %s" % keymap)


def write_keymap(keymap):
    mudur_file_path = os.path.join(consts.target_dir, "etc/conf.d/mudur")
    lines = []
    for l in open(mudur_file_path, "r").readlines():
        if l.strip().startswith('keymap=') or l.strip().startswith('#keymap='):
            l = 'keymap="%s"\n' % keymap
        lines.append(l)

    open(mudur_file_path, "w").writelines(lines)
