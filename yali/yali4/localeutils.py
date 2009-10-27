# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009, TUBITAK/UEKAE
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
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

import yali4.localedata
import yali4.sysutils
from yali4.constants import consts

def writeLocaleFromCmdline():
    locale_file_path = os.path.join(consts.target_dir, "etc/env.d/03locale")
    f = open(locale_file_path, "w")

    f.write("LANG=%s\n" % yali4.localedata.locales[consts.lang]["locale"])
    f.write("LC_ALL=%s\n" % yali4.localedata.locales[consts.lang]["locale"])

def setKeymap(keymap, variant=None):
    ad = ""
    if variant:
        ad = "-variant %s" % variant
    else:
        variant = ""
    yali4.sysutils.run("setxkbmap -layout %s %s" % (keymap,ad))
    yali4.sysutils.run("hav call zorg Xorg.Display setKeymap %s %s" % (keymap, variant))

def writeKeymap(keymap):
    mudur_file_path = os.path.join(consts.target_dir, "etc/conf.d/mudur")
    lines = []
    for l in open(mudur_file_path, "r").readlines():
        if l.strip().startswith('keymap=') or l.strip().startswith('# keymap='):
            l = 'keymap="%s"\n' % keymap
        if l.strip().startswith('language=') or l.strip().startswith('# language='):
            if consts.lang == "pt":
                l = 'language="pt_BR"\n'
            else:
                l = 'language="%s"\n' % consts.lang
        lines.append(l)

    open(mudur_file_path, "w").writelines(lines)
