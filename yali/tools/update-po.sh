#!/bin/bash

set -x

xgettext -L "python" -k__tr -k_ yali/gui/*.py yali/*.py -o po/yali.pot
msgmerge -U po/tr.po po/yali.pot
msgmerge -U po/nl.po po/yali.pot
