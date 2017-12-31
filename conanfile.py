#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Changelog
#
# v60.2
#
# - Incomplete data of ICU fixed upstream
#   Ticket http://bugs.icu-project.org/trac/ticket/13139
#
#

from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os
import glob

class IcuConan(ConanFile):
    name = "icu"
    version = "60.2"
    homepage = "http://site.icu-project.org"
    license = "http://www.unicode.org/copyright.html#License"
    description = "ICU is a mature, widely used set of C/C++ and Java libraries " \
                  "providing Unicode and Globalization support for software applications."
    url = "https://github.com/sigmoidal/conan-icu"
    settings = "os", "arch", "compiler", "build_type"
    source_url = "http://download.icu-project.org/files/icu4c/{0}/icu4c-{1}-src".format(version,version.replace('.', '_'))
    data_url = "http://download.icu-project.org/files/icu4c/{0}/icu4c-{1}-data".format(version,version.replace('.', '_'))

    exports_sources = [ "patches/*.patch" ]

    options = {"shared": [True, False],
               "data_packaging": [ "files", "archive", "library", "static" ],
               "with_unit_tests": [True, False],
               "silent": [True, False]}

    default_options = "shared=True", \
                      "data_packaging=archive", \
                      "with_unit_tests=False", \
                      "silent=True"
    
    # Dictionary storing strings useful for setting up the configuration and make command lines
    cfg = { 'enable_debug': '', 
            'platform': '', 
            'host': '', 
            'arch_bits': '',
            'output_dir': '', 
            'enable_static': '', 
            'data_packaging': '', 
            'general_opts': '' }

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("cygwin_installer/2.9.0@bincrafters/stable")
            if self.settings.compiler != "Visual Studio":
                self.build_requires("mingw_installer/1.0@conan/stable")

    def configure(self):
        if self.settings.compiler == "gcc" or self.settings.compiler == "clang":
            self.settings.compiler.libcxx = 'libstdc++11'

    def source(self):
        self.output.info("Fetching sources: {0}.tgz".format(self.source_url))
        tools.get("{0}.tgz".format(self.source_url))
        os.rename(self.name, 'sources')

    def build(self):
        self.update_config_files()

        patchfiles =  [
                        # see ICU Ticket: http://bugs.icu-project.org/trac/ticket/13469
                        # slated for inclusion in v61m1
                        'icu-60.1-msvc-escapesrc.patch',
                        '0014-mingwize-pkgdata.mingw.patch',
                        '0020-workaround-missing-locale.patch' ]

        if self.settings.compiler != 'Visual Studio' and self.settings.os == 'Windows':
            self.apply_patches(patchfiles)

        if self.settings.compiler == 'Visual Studio':
            runConfigureICU_file = os.path.join('sources', 'source','runConfigureICU')

            if self.settings.build_type == 'Release':
                tools.replace_in_file(runConfigureICU_file, "-MD", "-%s" % self.settings.compiler.runtime)
            if self.settings.build_type == 'Debug':
                tools.replace_in_file(runConfigureICU_file, "-MDd", "-%s -FS" % self.settings.compiler.runtime)
        #else:
        #    # This allows building ICU with multiple gcc compilers (overrides fixed compiler name gcc, i.e. gcc-5)
        #    runConfigureICU_file = os.path.join(self.name,'source','runConfigureICU')
        #    tools.replace_in_file(runConfigureICU_file, '        CC=gcc; export CC\n', '', strict=True)
        #    tools.replace_in_file(runConfigureICU_file, '        CXX=g++; export CXX\n', '', strict=True)

        self.cfg['icu_source_dir'] = os.path.join(self.build_folder, 'sources', 'source')
        self.cfg['build_dir'] = os.path.join(self.build_folder, 'sources', 'build')
        self.cfg['output_dir'] = os.path.join(self.build_folder, 'output')

        self.cfg['silent'] = '--silent' if self.options.silent else 'VERBOSE=1'
        self.cfg['enable_debug'] = '--enable-debug --disable-release' if self.settings.build_type == 'Debug' else ''
        self.cfg['arch_bits'] = '64' if self.settings.arch == 'x86_64' else '32'
        self.cfg['enable_static'] = '--enable-static --disable-shared' if not self.options.shared else '--enable-shared --disable-static'
        self.cfg['data_packaging'] = '--with-data-packaging={0}'.format(self.options.data_packaging)

        self.cfg['general_opts'] = '--disable-samples --disable-layout --disable-layoutex'
        if not self.options.with_unit_tests:
            self.cfg['general_opts'] += ' --disable-tests'

        if self.settings.compiler == 'Visual Studio':
            # this overrides pre-configured environments (such as Appveyor's)
            if "VisualStudioVersion" in os.environ:
                del os.environ["VisualStudioVersion"]
            self.cfg['vccmd'] = tools.vcvars_command(self.settings)
            self.build_cygwin_msvc()
        else:
            self.build_autotools()


    def package(self):
        self.copy("LICENSE", dst=".", src=os.path.join(self.source_folder, 'sources'))

        bin_dir_src, include_dir_src, lib_dir_src, share_dir_src = (os.path.join('output', path) for path in
                                                                    ('bin', 'include', 'lib', 'share'))
        if self.settings.os == 'Windows':
            bin_dir_dst, lib_dir_dst = ('bin64', 'lib64') if self.settings.arch == 'x86_64' else ('bin', 'lib')

            # we copy everything for a full ICU package
            self.copy("*", dst=bin_dir_dst, src=bin_dir_src, keep_path=True, symlinks=True)
            self.copy(pattern='*.dll', dst=bin_dir_dst, src=lib_dir_src, keep_path=False)
            self.copy("*", dst=lib_dir_dst, src=lib_dir_src, keep_path=True, symlinks=True)

            # lets remove .dlls from the lib dir, they are in bin/ in upstream releases.
            if os.path.exists(os.path.join(self.package_folder, lib_dir_dst)):
                for item in os.listdir(os.path.join(self.package_folder, lib_dir_dst)):
                    if item.endswith(".dll"):
                        os.remove(os.path.join(self.package_folder, lib_dir_dst, item))

            self.copy("*", dst="include", src=include_dir_src, keep_path=True, symlinks=True)
            self.copy("*", dst="share", src=share_dir_src, keep_path=True, symlinks=True)
        else:
            # we copy everything for a full ICU package
            self.copy("*", dst="bin", src=bin_dir_src, keep_path=True, symlinks=True)
            self.copy("*", dst="include", src=include_dir_src, keep_path=True, symlinks=True)
            self.copy("*", dst="lib", src=lib_dir_src, keep_path=True, symlinks=True)
            self.copy("*", dst="share", src=share_dir_src, keep_path=True, symlinks=True)


    def package_id(self):
        # ICU unit testing shouldn't affect the package's ID
        self.info.options.with_unit_tests = "any"

        # Verbosity doesn't affect package's ID
        self.info.options.silent = "any"


    def package_info(self):
        bin_dir, lib_dir = ('bin64', 'lib64') if self.settings.arch == 'x86_64' and self.settings.os == 'Windows' else ('bin' , 'lib')
        self.cpp_info.libdirs = [ lib_dir ]

        # if icudata is not last, it fails to build on some platforms (Windows)
        # some linkers are not clever enough to be able to link
        self.cpp_info.libs = []
        vtag = self.version.split('.')[0]
        keep = False
        for lib in tools.collect_libs(self, lib_dir):
            if not vtag in lib:
                if 'icudata' in lib or 'icudt' in lib:
                    keep = lib
                else:
                    self.cpp_info.libs.append(lib)

        if keep:
            self.cpp_info.libs.append(keep)

        data_dir = os.path.join(self.package_folder, 'share', self.name, self.version)
        data_file = "icudt{v}l.dat".format(v=vtag)
        data_path = os.path.join(data_dir, data_file).replace('\\', '/')
        self.env_info.ICU_DATA.append(data_path)

        self.env_info.PATH.append(os.path.join(self.package_folder, bin_dir))

        if not self.options.shared:
            self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION")
            if self.settings.os == 'Linux':
                self.cpp_info.libs.append('dl')
                
            if self.settings.os == 'Windows':
                self.cpp_info.libs.append('advapi32')
                
        if self.settings.compiler == "gcc" or self.settings.compiler == "clang":
            self.cpp_info.cppflags = ["-std=c++11"]


    def update_config_files(self):
        # update the outdated config.guess and config.sub included in ICU
        # ICU Ticket: http://bugs.icu-project.org/trac/ticket/13470
        # slated for fix in v61.1
        config_updates = ['config.guess', 'config.sub']
        for cfg_update in config_updates:
            dst_config = os.path.join('sources', cfg_update)
            if os.path.isfile(dst_config):
                os.remove(dst_config)
            self.output.info('Updating %s' % dst_config)
            tools.download('http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f={0};hb=HEAD'.format(cfg_update),
                           dst_config)

    def apply_patches(self,patchfiles):
        for patch in patchfiles:
            patchfile = os.path.join('patches',patch)
            tools.patch(base_path=os.path.join('sources'), patch_file=patchfile, strip=1)


    def build_config_cmd(self):
        outdir = self.cfg['output_dir'].replace('\\', '/')

        #outdir = tools.unix_path(self.cfg['output_dir'])

        #if self.options.msvc_platform == 'cygwin':
        #outdir = re.sub(r'([a-z]):(.*)',
        #                '/cygdrive/\\1\\2',
        #                self.cfg['output_dir'],
        #                flags=re.IGNORECASE).replace('\\', '/')


        config_cmd = "../source/runConfigureICU {enable_debug} " \
                     "{platform} {host} {lib_arch_bits} {outdir} " \
                     "{enable_static} {data_packaging} {general}" \
                     "".format(enable_debug=self.cfg['enable_debug'],
                               platform=self.cfg['platform'],
                               host=self.cfg['host'],
                               lib_arch_bits='--with-library-bits=%s' % self.cfg['arch_bits'],
                               outdir='--prefix=%s' % outdir,
                               enable_static=self.cfg['enable_static'],
                               data_packaging=self.cfg['data_packaging'],
                               general=self.cfg['general_opts'])

        return config_cmd


    def build_cygwin_msvc(self):
        self.cfg['platform'] = 'Cygwin/MSVC'

        if 'CYGWIN_ROOT' not in os.environ:
            raise Exception("CYGWIN_ROOT environment variable must be set.")
        else:
            self.output.info("Using Cygwin from: " + os.environ["CYGWIN_ROOT"])

        os.environ['PATH'] = os.path.join(os.environ['CYGWIN_ROOT'], 'bin') + os.pathsep + \
                             os.path.join(os.environ['CYGWIN_ROOT'], 'usr', 'bin') + os.pathsep + \
                             os.environ['PATH']

        os.mkdir(self.cfg['build_dir'])

        self.output.info("Starting configuration.")

        config_cmd = self.build_config_cmd()
        self.run("{vccmd} && cd {builddir} && bash -c '{config_cmd}'".format(vccmd=self.cfg['vccmd'],
                                                                             builddir=self.cfg['build_dir'],
                                                                             config_cmd=config_cmd))

        self.output.info("Starting built.")

        self.run("{vccmd} && cd {builddir} && make {silent} -j {cpus_var}".format(vccmd=self.cfg['vccmd'],
                                                                                  builddir=self.cfg['build_dir'],
                                                                                  silent=self.cfg['silent'],
                                                                                  cpus_var=tools.cpu_count()))
        if self.options.with_unit_tests:
            self.run("{vccmd} && cd {builddir} && make {silent} check".format(vccmd=self.cfg['vccmd'],
                                                                              builddir=self.cfg['build_dir'],
                                                                              silent=self.cfg['silent']))

        self.run("{vccmd} && cd {builddir} && make {silent} install".format(vccmd=self.cfg['vccmd'],
                                                                            builddir=self.cfg['build_dir'],
                                                                            silent=self.cfg['silent']))
            

    def build_autotools(self):
        env_build = AutoToolsBuildEnvironment(self)
        if not self.options.shared:
            env_build.defines.append("U_STATIC_IMPLEMENTATION")

        with tools.environment_append(env_build.vars):
            if self.settings.os == 'Linux':
                self.cfg['platform'] = 'Linux/gcc' if str(self.settings.compiler).startswith('gcc') else 'Linux'
            elif self.settings.os == 'Macos':
                self.cfg['platform'] = 'MacOSX'
            if self.settings.os == 'Windows':
                self.cfg['platform'] = 'MinGW'

                if self.settings.arch == 'x86':
                    MINGW_CHOST = 'i686-w64-mingw32'
                else:
                    MINGW_CHOST = 'x86_64-w64-mingw32'

                self.cfg['host'] = '--build={MINGW_CHOST} ' \
                                   '--host={MINGW_CHOST} '.format(MINGW_CHOST=MINGW_CHOST)

            os.mkdir(self.cfg['build_dir'])

            config_cmd = self.build_config_cmd()

            # with tools.environment_append(env_build.vars):
            self.run("cd {builddir} && bash -c '{config_cmd}'".format(builddir=self.cfg['build_dir'],
                                                                 config_cmd=config_cmd))

            os.system("cd {builddir} && make {silent} -j {cpus_var}".format(builddir=self.cfg['build_dir'],
                                                                            cpus_var=tools.cpu_count(),
                                                                            silent=self.cfg['silent']))

            if self.options.with_unit_tests:
                os.system("cd {builddir} && make {silent} check".format(builddir=self.cfg['build_dir'],
                                                                       silent=self.cfg['silent']))

            os.system("cd {builddir} && make {silent} install".format(builddir=self.cfg['build_dir'],
                                                                     silent=self.cfg['silent']))

            if self.settings.os == 'Macos':
                with tools.chdir('output/lib'):
                    for dylib in glob.glob('*icu*.{0}.dylib'.format(self.version)):
                        self.run('install_name_tool -id {0} {1}'.format(
                            os.path.basename(dylib), dylib))
