#!/bin/bash

LANGUAGES=`ls po/*.po`

set -x

xgettext -L "python" -k__tr -k_ yali/gui/Ui/*.py yali/gui/*.py yali/*.py -o po/yali.pot
for lang in $LANGUAGES
do
    msgmerge -U $lang po/yali.pot
done

