#!/bin/bash

LANGUAGES=`ls po/*.po`
TEMP=`mktemp`
set -x

xgettext -L "python" -k__tr -k_ yali4/gui/Ui/*.py yali4/gui/*.py yali4/*.py -o po/yali4.pot
for lang in $LANGUAGES
do
    #msgcat --use-first -o $TEMP $lang po/yali4.pot
    msgmerge -q -o $TEMP $lang po/yali4.pot
    cat $TEMP > $lang
done
rm -f $TEMP
