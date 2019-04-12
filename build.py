#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from bincrafters import build_template_default, build_template_installer

if __name__ == "__main__":

    if "ARCH" in os.environ:
        arch = os.environ["ARCH"]
        builder = build_template_installer.get_builder()
        builder.add({"os" : build_shared.get_os(), "arch_build" : arch, "arch": arch}, {}, {}, {})
    else:
        builder = build_template_default.get_builder(pure_c=False)

    builder.run()
