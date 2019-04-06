# -*- coding: utf-8 -*-

import os
import glob
from conans import ConanFile, tools, AutoToolsBuildEnvironment


class ICUConan(ConanFile):
    name = "icu"
    version = "63.1"
    homepage = "http://site.icu-project.org"
    license = "ICU"
    description = "ICU is a mature, widely used set of C/C++ and Java libraries " \
                  "providing Unicode and Globalization support for software applications."
    url = "https://github.com/bincrafters/conan-icu"
    settings = "os", "arch", "compiler", "build_type"
    topics = ("conan", "icu", "icu4c", "i see you", "unicode")
    author = "Bincrafters <bincrafters@gmail.com>"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "data_packaging": ["files", "archive", "library", "static"],
               "with_unit_tests": [True, False],
               "silent": [True, False]}
    default_options = {"shared": False,
                       "fPIC": True,
                       "data_packaging": "archive",
                       "with_unit_tests": False,
                       "silent": True}
    exports = ["LICENSE.md"]
    exports_sources = ["patches/*.patch"]
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    @property
    def _is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc"

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("cygwin_installer/2.9.0@bincrafters/stable")
            if self.settings.compiler == "gcc" and tools.os_info.is_windows:
                self.build_requires("mingw_installer/1.0@conan/stable")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        version = self.version.replace('.', '-')
        source_url = "https://github.com/unicode-org/icu/archive/release-{0}.tar.gz".format(version)
        tools.get("{0}".format(source_url),
                  sha256="9a3be16d772be2817854ef4dcb45fb7fea669ca7ca592e039264239c1acd415f")
        os.rename("{0}-release-{1}".format(self.name, version), self._source_subfolder)

    def _replace_pythonpath(self):
        if self._is_msvc:
            srcdir = os.path.join(self.build_folder, self._source_subfolder, "icu4c", "source")
            configure = os.path.join(self._source_subfolder, "icu4c", "source", "configure")
            tools.replace_in_file(configure,
                                  'PYTHONPATH="$srcdir/data"',
                                  'PYTHONPATH="%s\\data"' % srcdir)
            tools.replace_in_file(configure,
                                  'PYTHONPATH="$srcdir/test/testdata:$srcdir/data"',
                                  'PYTHONPATH="%s\\test\\testdata;%s\\data"' % (srcdir, srcdir))

    def build(self):
        for filename in glob.glob("patches/*.patch"):
            self.output.info('applying patch "%s"' % filename)
            tools.patch(base_path=self._source_subfolder, patch_file=filename)

        if self._is_msvc:
            run_configure_icu_file = os.path.join(self._source_subfolder, 'icu4c', 'source', 'runConfigureICU')

            flags = "-%s" % self.settings.compiler.runtime
            if self.settings.build_type == 'Debug':
                flags += " -FS"
            tools.replace_in_file(run_configure_icu_file, "-MDd", flags)
            tools.replace_in_file(run_configure_icu_file, "-MD", flags)

        # self._replace_pythonpath() # ICU 64.1

        env_build = AutoToolsBuildEnvironment(self)
        if not self.options.shared:
            env_build.defines.append("U_STATIC_IMPLEMENTATION")
        if tools.is_apple_os(self.settings.os) and self.settings.get_safe("os.version"):
            env_build.flags.append(tools.apple_deployment_target_flag(self.settings.os,
                                                                      self.settings.os.version))

        build_dir = os.path.join(self.build_folder, self._source_subfolder, 'icu4c', 'build')
        os.mkdir(build_dir)

        with tools.vcvars(self.settings) if self._is_msvc else tools.no_op():
            with tools.environment_append(env_build.vars):
                with tools.chdir(build_dir):
                    self.run(self._build_config_cmd(), win_bash=tools.os_info.is_windows)
                    silent = '--silent' if self.options.silent else 'VERBOSE=1'
                    command = "make {silent} -j {cpu_count}".format(silent=silent,
                                                                    cpu_count=tools.cpu_count())
                    self.run(command, win_bash=tools.os_info.is_windows)
                    if self.options.with_unit_tests:
                        command = "make {silent} check".format(silent=silent)
                        self.run(command, win_bash=tools.os_info.is_windows)
                    command = "make {silent} install".format(silent=silent)
                    self.run(command, win_bash=tools.os_info.is_windows)

        self._install_name_tool()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=os.path.join(self.source_folder, self._source_subfolder, 'icu4c'))

    def package_id(self):
        self.info.options.with_unit_tests = "any"  # ICU unit testing shouldn't affect the package's ID
        self.info.options.silent = "any"  # Verbosity doesn't affect package's ID

    def package_info(self):
        def lib_name(lib):
            name = lib
            if self._is_msvc:
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

        data_dir = os.path.join(self.package_folder, 'share', self.name, self.version)
        vtag = self.version.split('.')[0]
        data_file = "icudt{v}l.dat".format(v=vtag)
        data_path = os.path.join(data_dir, data_file).replace('\\', '/')
        self.env_info.ICU_DATA.append(data_path)
        self.env_info.PATH.append(os.path.join(self.package_folder, 'bin'))

        if not self.options.shared:
            self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION")
        if self.settings.os == 'Linux':
            self.cpp_info.libs.append('dl')

        if self.settings.os == 'Windows':
            self.cpp_info.libs.append('advapi32')

    def _build_config_cmd(self):
        prefix = self.package_folder.replace('\\', '/')

        platform = {("Windows", "Visual Studio"): "Cygwin/MSVC",
                    ("Windows", "gcc"): "MinGW",
                    ("Linux", "gcc"): "Linux/gcc",
                    ("Linux", "clang"): "Linux",
                    ("Macos", "gcc"): "MacOSX",
                    ("Macos", "clang"): "MacOSX",
                    ("Macos", "apple-clang"): "MacOSX"}.get((str(self.settings.os),
                                                             str(self.settings.compiler)))

        bits = "64" if self.settings.arch == "x86_64" else "32"
        args = [platform,
                "--prefix={0}".format(prefix),
                "--with-data-packaging={0}".format(self.options.data_packaging),
                "--with-library-bits={0}".format(bits),
                "--disable-samples",
                "--disable-layout",
                "--disable-layoutex"]

        if self._is_mingw:
            mingw_chost = 'i686-w64-mingw32' if self.settings.arch == 'x86' else 'x86_64-w64-mingw32'
            args.extend(["--build={0}".format(mingw_chost),
                         "--host={0}".format(mingw_chost)])

        if self.settings.build_type == "Debug":
            args.extend(["--disable-release", "--enable-debug"])
        if self.options.shared:
            args.extend(["--disable-static", "--enable-shared"])
        else:
            args.extend(["--enable-static", "--disable-shared"])
        if not self.options.with_unit_tests:
            args.append('--disable-tests')

        config_cmd = "../source/runConfigureICU %s" % " ".join(args)

        return config_cmd

    def _install_name_tool(self):
        if tools.is_apple_os(self.settings.os):
            with tools.chdir(os.path.join(self.package_folder, 'lib')):
                for dylib in glob.glob('*icu*.{0}.dylib'.format(self.version)):
                    command = 'install_name_tool -id {0} {1}'.format(os.path.basename(dylib), dylib)
                    self.output.info(command)
                    self.run(command)
