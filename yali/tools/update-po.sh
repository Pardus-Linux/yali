#!/bin/bash

LANGUAGES="tr nl fr de"

set -x

xgettext -L "python" -k__tr -k_ yali/gui/Ui/*.py yali/gui/*.py yali/*.py -o po/yali.pot
for lang in $LANGUAGES
do
    msgmerge -U po/$lang.po po/yali.pot
done

