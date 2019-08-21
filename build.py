#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import platform
from bincrafters import (build_template_default,
                         build_template_installer,
                         build_shared)

if __name__ == "__main__":

    if "ARCH" in os.environ:
        arch = os.environ["ARCH"]
        builder = build_template_installer.get_builder()
        builder.add({"os": build_shared.get_os(),
                     "arch_build": arch,
                     "arch": arch},
                    {}, {}, {})
    else:
        builder = build_template_default.get_builder(pure_c=False)
        if platform.system() == "Darwin":
            # add builds with cppstd=11
            filtered_builds = []
            for settings, options, env_vars, build_requires in builder.builds:
                settings_cppstd = settings.copy()
                settings_cppstd["compiler.cppstd"] = 11
                filtered_builds.append([settings_cppstd, options, env_vars, build_requires])
                filtered_builds.append([settings, options, env_vars, build_requires])
            builder.builds = filtered_builds
        if platform.system() == "Linux":
            # add builds with libstdc++11
            filtered_builds = []
            for settings, options, env_vars, build_requires in builder.builds:
                if (settings["compiler"] == "clang") and (float(settings["compiler.version"]) >= 6):
                    settings_libstdcxx11 = settings.copy()
                    settings_libstdcxx11["compiler.libcxx"] = "libstdc++11"
                    filtered_builds.append([settings_libstdcxx11, options, env_vars, build_requires])
                filtered_builds.append([settings, options, env_vars, build_requires])
            builder.builds = filtered_builds

    builder.run()
