import os
from icu_base import ICUBase


class ICUConan(ICUBase):
    name = "icu"
    version = ICUBase.version
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "data_packaging": ["files", "archive", "library", "static"],
               "with_extras": [True, False],
               "with_unit_tests": [True, False],
               "silent": [True, False]}
    default_options = {"shared": False,
                       "fPIC": True,
                       "data_packaging": "archive",
                       "with_extras": True,
                       "with_unit_tests": False,
                       "silent": True}
    generators = 'txt', 'virtualenv'

    def build_requirements(self):
        super(ICUConan, self).build_requirements()
        if self.cross_building:
            self.build_requires("icu_installer/%s@bincrafters/stable" % self.version)

    def package_id(self):
        del self.info.options.with_unit_tests  # ICU unit testing shouldn't affect the package's ID
        del self.info.options.silent  # Verbosity doesn't affect package's ID

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @property
    def build_config_args(self):
        args = super(ICUConan, self).build_config_args
        if self.cross_building:
            args.append("--with-cross-build=%s" % self.deps_cpp_info["icu_installer"].rootpath)
        return args

    def package_info(self):
        def lib_name(lib):
            name = lib
            if self.settings.os == "Windows":
                if not self.options.shared:
                    name = 's' + name
                if self.settings.build_type == "Debug":
                    name += 'd'
            return name

        libs = ['icuin' if self.settings.os == "Windows" else 'icui18n',
                'icuio', 'icutest', 'icutu', 'icuuc',
                'icudt' if self.settings.os == "Windows" else 'icudata']
        self.cpp_info.libs = [lib_name(lib) for lib in libs]
        self.cpp_info.bindirs.append('lib')

        data_dir_name = self.name
        if self.settings.os == "Windows" and self.settings.build_type == "Debug":
            data_dir_name += 'd'
        data_dir = os.path.join(self.package_folder, 'share', data_dir_name, self.version)
        vtag = self.version.split('.')[0]
        data_file = "icudt{v}l.dat".format(v=vtag)
        data_path = os.path.join(data_dir, data_file).replace('\\', '/')
        if self.options.get_safe("data_packaging") in ["files", "archive"]:
            self.env_info.ICU_DATA.append(data_path)

        if not self.options.shared:
            self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION")
        if self.settings.os == 'Linux':
            self.cpp_info.libs.append('dl')

        if self.settings.os == 'Windows':
            self.cpp_info.libs.append('advapi32')
