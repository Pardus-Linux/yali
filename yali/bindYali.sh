#!/bin/bash

cp -rf /usr/lib/python2.6/site-packages/yali4/ /yali
mount --bind /yali/ /usr/lib/python2.6/site-packages/yali4/

echo "Yali is ready in /yali ..."
