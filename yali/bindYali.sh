#!/bin/bash

cp -rf /usr/lib/python2.6/site-packages/yali/ /yali
mount --bind /yali/ /usr/lib/python2.6/site-packages/yali/

echo "Yali is ready in /yali ..."
