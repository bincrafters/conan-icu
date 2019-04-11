# -*- coding: utf-8 -*-

from icu_base import ICUBase
import os


class ICUInstallerConan(ICUBase):
    name = "icu_installer"
    version = ICUBase.version
    settings = "os_build", "arch_build", "compiler"

    def package_id(self):
        del self.info.settings.compiler

    def package_info(self):
        self.env_info.PATH.append(os.path.join(self.package_folder, 'bin'))
