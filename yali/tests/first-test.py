#!/usr/bin/python
# -*- coding: utf-8 -*-

from nose.tools import *

class TestMain(object):
    def test_main():
        main()
        assert ctx.flags
