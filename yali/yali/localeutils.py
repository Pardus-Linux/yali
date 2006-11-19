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

import yali.localedata
from yali.constants import consts



def write_locale_from_cmdline():
    locale_file_path = os.path.join(consts.target_dir, "etc/env.d/03locale")
    f = open(locale_file_path, "w")

    f.write("LANG=%s\n" % yali.localedata[consts.lang]["locale"])
    f.write("LC_ALL=%s\n" % yali.localedata[consts.lang]["locale"])



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
