#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile


class TestPackageConan(ConanFile):

    def test(self):
        self.run("uconv --version")
