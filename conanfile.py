from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os
import glob
import shutil


#
# Refer to http://userguide.icu-project.org/icudata for the data_packaging option
#
# Note that the default MSVC builds (msvc_platform=visual_studio) with Visual Studio cannot do static ICU builds
#
# Using the with_data option fetches the complete ICU data package, at the expense of size
#
# If you're building with Cygwin, the environment variable CYGWIN_ROOT must be present or specified via the command line
#
# If you're building with MSYS, the environment variable MSYS_ROOT must be present or specified via the command line
#
# examples:
#
# To update the conanfile.py without rebuilding:
#
#    conan export icu/59.1@cygwin/icu -k && conan package icu/59.1@cygwin/icu addc9b54f567a693944ffcc56568c29b0d0926c8
#
# for creating a tgz:
#
#    conan upload --skip_upload icu/59.1@cygwin/icu -p addc9b54f567a693944ffcc56568c29b0d0926c8
#
# Create an ICU package using a Cygwin/MSVC static release built
#
#    conan create cygwin/icu -o icu:msvc_platform=cygwin -o icu:shared=False -e CYGWIN_ROOT=D:\PortableApps\CygwinPortable\App\Cygwin
#
# Create an ICU package using a Cygwin/MSVC static debug built
#
#    conan create cygwin/icu -o icu:msvc_platform=cygwin -s icu:build_type=Debug -o icu:shared=False
#
# Create an ICU package using a Cygwin/MSYS static debug built
#
#    conan create msys/icu -o icu:msvc_platform=msys -o icu:with_data=True -e MSYS_ROOT=D:\dev\msys64
#
#
# Create an ICU package using a Cygwin/MSVC static debug built with static runtimes
#
#    conan create cygwin/icu -o icu:msvc_platform=cygwin -o icu:shared=False  -s compiler.runtime=MTd -s build_type=Debug -e CYGWIN_ROOT=D:\PortableApps\CygwinPortable\App\Cygwin
#

class IcuConan(ConanFile):
    name = "icu"
    version = "59.1"
    license = "http://www.unicode.org/copyright.html#License"
    description = "ICU is a mature, widely used set of C/C++ and Java libraries providing Unicode and Globalization support for software applications."
    url = "https://github.com/bincrafters/conan-icu"
    settings = "os", "arch", "compiler", "build_type"
    source_url = "http://download.icu-project.org/files/icu4c/{0}/icu4c-{1}-src".format(version,
                                                                                        version.replace('.', '_'))
    data_url = "http://download.icu-project.org/files/icu4c/{0}/icu4c-{1}-data".format(version,
                                                                                       version.replace('.', '_'))

    options = {"with_io": [True, False],
               "with_data": [True, False],
               "shared": [True, False],
               "msvc_platform": ["visual_studio", "cygwin", "msys"],
               "data_packaging": ["shared", "static", "files", "archive"],
               "with_msys": [True, False],
               "with_unit_tests": [True, False]}

    default_options = "with_io=False", \
                      "with_data=False", \
                      "shared=True", \
                      "msvc_platform=visual_studio", \
                      "data_packaging=archive", \
                      "with_msys=False", \
                      "with_unit_tests=False"

    def requirements(self):
        if self.options.with_msys:
            self.requires.add("msys_installer/latest@bincrafters/stable")

    def source(self):
        archive_type = "zip"
        if self.settings.os != 'Windows' or self.options.msvc_platform != 'visual_studio':
            archive_type = "tgz"

        self.output.info("Fetching sources: {0}.{1}".format(self.source_url, archive_type))

        tools.get("{0}.{1}".format(self.source_url, archive_type))
        tools.download(r'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD',
                       'config.guess')
        tools.download(r'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD',
                       'config.sub')

        if self.options.with_data:
            tools.get("{0}.zip".format(self.data_url))

    def build(self):
        root_path = self.conanfile_directory
        src_path = os.path.join(root_path, self.name, 'source')

        if self.options.with_data:
            # We add the whole data within the source tree
            src_datadir = os.path.join(root_path, 'data')
            dst_datadir = os.path.join(src_path, 'data')

            os.rename(dst_datadir, dst_datadir + "-bak")
            os.rename(src_datadir, dst_datadir)
        else:
            tools.replace_in_file(
                os.path.join(src_path, 'data', 'makedata.mak'),
                r'GODATA "$(ICU_LIB_TARGET)" "$(TESTDATAOUT)\testdata.dat"',
                r'GODATA "$(ICU_LIB_TARGET)"')

        # to be improved
        src_config_guess = os.path.join(root_path, 'config.guess')
        src_config_sub = os.path.join(root_path, 'config.sub')

        dst_config_guess = os.path.join(root_path, self.name, 'source', 'config.guess')
        dst_config_sub = os.path.join(root_path, self.name, 'source', 'config.sub')

        if os.path.isfile(dst_config_guess):
            os.remove(dst_config_guess)

        if os.path.isfile(dst_config_sub):
            os.remove(dst_config_sub)

        shutil.copy(src_config_guess, dst_config_guess)
        shutil.copy(src_config_sub, dst_config_sub)

        self.output.info("Copy src: " + src_config_guess)
        self.output.info("Copy dst: " + dst_config_guess)
        self.output.info("Copy src: " + src_config_sub)
        self.output.info("Copy dst: " + dst_config_sub)

        # This handles the weird case of using ICU sources for Windows on a Unix environment, and vice-versa
        # this is primarily aimed at builds using Cygwin/MSVC which require unix line endings
        if self.settings.os != 'Windows' or self.options.msvc_platform != 'visual_studio':
            if b'\r\n' in open(os.path.join(src_path, "runConfigureICU"), 'rb').read():
                self.output.error("\n\nBuild failed. The line endings of your sources are inconsistent with the build configuration you requested. \
                                   \nPlease consider clearing your cache sources (i.e. remove the --keep-sources command line option\n\n")
                return
        else:
            if b'\r\n' not in open(os.path.join(src_path, "runConfigureICU"), 'rb').read():
                self.output.error("\n\nBuild failed. The line endings of your sources are inconsistent with the build configuration you requested. \
                                   \nPlease consider clearing your cache sources (i.e. remove the --keep-sources command line option\n\n")
                return

        if self.settings.os == 'Windows':
            vcvars_command = tools.vcvars_command(self.settings)
            if self.options.msvc_platform == 'cygwin':
                platform = 'Cygwin/MSVC'

                arch = '64' if self.settings.arch == 'x86_64' else '32'
                enable_debug = '--enable-debug --disable-release' if self.settings.build_type == 'Debug' else ''
                enable_static = '--enable-static --disable-shared' if not self.options.shared else '--enable-shared --disable-static'
                data_packaging = '--with-data-packaging={0}'.format(self.options.data_packaging)

                if not self.options.shared:
                    self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION")

                # try to detect if Cygwin is available
                if 'CYGWIN_ROOT' in os.environ:
                    if not os.path.isdir(os.path.join(os.environ["CYGWIN_ROOT"], "bin")):
                        self.output.error(
                            'Cygwin cannot be found on your system. To build ICU with Cygwin/MSVC you need a Cygwin installation (see http://cygwin.com/).')
                        return
                else:
                    if os.path.isdir(r'C:\\Cygwin'):
                        self.output.info(r'Detected an installation of Cygwin in C:\\Cygwin')
                        os.environ["CYGWIN_ROOT"] = r'C:\\Cygwin'

                if 'CYGWIN_ROOT' not in os.environ:
                    self.output.warn('CYGWIN_ROOT not in your environment')
                else:
                    self.output.info("Using Cygwin from: " + os.environ["CYGWIN_ROOT"])

                cygwin_root_path = os.environ["CYGWIN_ROOT"].replace('\\', '/')

                os.environ["PATH"] = os.pathsep.join(r"C:\\Windows\\system32",
                                                     r"C:\\Windows",
                                                     r"C:\\Windows\\system32\Wbem",
                                                     cygwin_root_path + "/bin",
                                                     cygwin_root_path + "/usr/bin",
                                                     cygwin_root_path + "/usr/sbin")

                output_path = os.path.join(root_path, 'output')
                root_path = root_path.replace('\\', '/')
                output_path = output_path.replace('\\', '/')

                configfile = os.path.join(root_path, self.name, 'source', 'runConfigureICU')
                runtime = self.settings.compiler.runtime
                if self.settings.build_type == 'Release':
                    tools.replace_in_file(configfile, "-MD", "-%s" % runtime)
                if self.settings.build_type == 'Debug':
                    tools.replace_in_file(configfile, "-MDd", "-%s" % runtime)

                b_path = os.path.join(root_path, self.name, 'build')
                os.mkdir(b_path)
                self.output.info("Starting configuration.")
                self.run(
                    "{0} && cd {1} && bash ../source/runConfigureICU {2} {3} --with-library-bits={4} --prefix={5} {6} {7} --disable-layout --disable-layoutex".format(
                        vcvars_command, b_path, enable_debug, platform, arch, output_path, enable_static,
                        data_packaging))
                self.output.info("Starting build.")
                # do not use multiple CPUs with make (make -j X) as builds fail on Cygwin
                self.run("{0} && cd {1} && make --silent".format(vcvars_command, b_path))
                if self.options.with_unit_tests:
                    self.run("{0} && cd {1} && make check".format(vcvars_command, b_path))
                self.run("{0} && cd {1} && make install".format(vcvars_command, b_path))
            elif self.options.msvc_platform == 'msys':
                platform = 'MSYS/MSVC'

                arch = '64' if self.settings.arch == 'x86_64' else '32'
                enable_debug = '--enable-debug --disable-release' if self.settings.build_type == 'Debug' else ''
                enable_static = '--enable-static --disable-shared' if not self.options.shared else '--enable-shared --disable-static'
                data_packaging = '--with-data-packaging={0}'.format(self.options.data_packaging)

                if not self.options.shared:
                    self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION")

                # try to detect if MSYS is available
                if 'MSYS_ROOT' in os.environ:
                    if not os.path.isdir(os.path.join(os.environ["MSYS_ROOT"], 'usr', 'bin')):
                        self.output.error(
                            'MSYS cannot be found on your system. To build ICU with MSYS/MSVC you need an MSYS installation (see http://www.msys2.org).')
                        return
                else:
                    if os.path.isdir(r'C:\\msys64'):
                        self.output.info(r'Detected an installation of MSYS in C:\\msys64')
                        os.environ["MSYS_ROOT"] = r'C:\\msys64'

                if 'MSYS_ROOT' not in os.environ:
                    self.output.warn('MSYS_ROOT not in your environment')
                else:
                    self.output.info("Using MSYS from: " + os.environ["MSYS_ROOT"])

                msys_root_path = os.environ["MSYS_ROOT"].replace('\\', '/')

                self.output.info("MSYS_ROOT: " + os.environ["MSYS_ROOT"])
                self.output.info("msys_root_path: " + msys_root_path)
                self.output.info("msys_root_path/bin: " + os.path.join(msys_root_path, 'usr', 'bin'))

                os.environ["PATH"] = os.pathsep.join(r"C:\\Windows\\system32",
                                                     r"C:\\Windows",
                                                     r"C:\\Windows\\system32\Wbem",
                                                     os.path.join(msys_root_path, 'usr', 'bin'))

                self.output.info("PATH: " + os.environ["PATH"])
                output_path = os.path.join(root_path, 'output')
                root_path = root_path.replace('\\', '/')
                output_path = output_path.replace('\\', '/')

                configfile = os.path.join(root_path, self.name, 'source', 'runConfigureICU')
                runtime = self.settings.compiler.runtime
                if self.settings.build_type == 'Release':
                    tools.replace_in_file(configfile, "-MD", "-%s" % runtime)
                if self.settings.build_type == 'Debug':
                    tools.replace_in_file(configfile, "-MDd", "-%s -FS" % runtime)

                b_path = os.path.join(root_path, self.name, 'build')
                b_path = b_path.replace('\\', '/')
                os.mkdir(b_path)

                apply_msys_config_detection_patch = '--host=i686-pc-mingw{0}'.format(arch)

                self.run(
                    "{0} && bash -c ^'cd {1} ^&^& ../source/runConfigureICU {2} {3} {4} --with-library-bits={5} --prefix={6} {7} {8} --disable-layout --disable-layoutex^'".format(
                        vcvars_command, b_path, enable_debug, platform, apply_msys_config_detection_patch, arch,
                        output_path, enable_static, data_packaging))

                # There is a fragment in Makefile.in:22 of ICU that prevents from building with MSYS:
                #
                # ifneq (@platform_make_fragment_name@,mh-cygwin-msvc)
                # SUBDIRS += escapesrc
                # endif
                #
                # We patch the respective Makefile.in, to disable building it for MSYS
                #
                escapesrc_patch = os.path.join(root_path, self.name, 'source', 'tools', 'Makefile.in')
                tools.replace_in_file(escapesrc_patch, 'SUBDIRS += escapesrc',
                                      '\tifneq (@platform_make_fragment_name@,mh-msys-msvc)\n\t\tSUBDIRS += escapesrc\n\tendif')

                self.run("{0} && bash -c ^'cd {1} ^&^& make --silent -j {2}".format(vcvars_command, b_path,
                                                                                    tools.cpu_count()))
                if self.options.with_unit_tests:
                    self.run("{0} && bash -c ^'cd {1} ^&^& make check".format(vcvars_command, b_path))

                self.run("{0} && bash -c ^'cd {1} ^&^& make install'".format(vcvars_command, b_path))
            else:
                sln_file = os.path.join(src_path, "allinone", "allinone.sln")
                targets = ["i18n", "common", "pkgdata"]
                if self.options.with_io:
                    targets.append('io')

                build_command = tools.build_sln_command(self.settings, sln_file, targets=targets, upgrade_project=False)
                build_command = build_command.replace('"x86"', '"Win32"')
                command = "{0} && {1}".format(vcvars_command, build_command)
                self.run(command)
                cfg = 'x64' if self.settings.arch == 'x86_64' else 'x86'
                cfg += "\\" + str(self.settings.build_type)
                data_dir = src_path + "\\data"
                bin_dir = data_dir + "\\..\\..\\bin"
                if self.settings.arch == 'x86_64':
                    bin_dir += '64'

                makedata = '{vcvars} && cd {datadir} && nmake /a /f makedata.mak ICUMAKE="{datadir}" CFG={cfg}'.format(
                    vcvars=vcvars_command,
                    datadir=data_dir,
                    cfg=cfg)
                self.output.info(makedata)
                self.run(makedata)
        else:
            env_build = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env_build.vars):
                platform = ''
                if self.settings.os == 'Linux':
                    if self.settings.compiler == 'gcc':
                        platform = 'Linux/gcc'
                    else:
                        platform = 'Linux'
                elif self.settings.os == 'Macos':
                    platform = 'MacOSX'

                arch = '64' if self.settings.arch == 'x86_64' else '32'
                enable_debug = '--enable-debug --disable-release' if self.settings.build_type == 'Debug' else ''
                enable_static = '--enable-static --disable-shared' if not self.options.shared else '--enable-shared --disable-static'
                data_packaging = '--with-data-packaging={0}'.format(self.options.data_packaging)

                b_path = os.path.join(root_path, self.name, 'build')
                os.mkdir(b_path)

                output_path = os.path.join(root_path, 'output')

                self.run(
                    "cd {0} && bash ../source/runConfigureICU {1} {2} --with-library-bits={3} --prefix={4} {5} {6} --disable-layout --disable-layoutex".format(
                        b_path, enable_debug, platform, arch, output_path, enable_static, data_packaging))
                self.run("cd {0} && make --silent -j {1} install".format(b_path, tools.cpu_count()))

                if self.settings.os == 'Macos':
                    with tools.chdir('output/lib'):
                        for dylib in glob.glob('*icu*.{0}.dylib'.format(self.version)):
                            self.run('install_name_tool -id {0} {1}'.format(
                                os.path.basename(dylib), dylib))

    def package(self):
        # self.options.msvc_platform = 'cygwin'
        # self.options.data_packaging = 'archive'
        # self.options.shared = False

        if self.settings.os == 'Windows':
            if self.options.msvc_platform == 'cygwin' or self.options.msvc_platform == 'msys':

                bin_dir, include_dir, lib_dir, share_dir = (os.path.join('output', path) for path in
                                                            ('bin', 'include', 'lib', 'share'))
                self.output.info('bin_dir = {0}'.format(bin_dir))
                self.output.info('include_dir = {0}'.format(include_dir))
                self.output.info('lib_dir = {0}'.format(lib_dir))
                self.output.info('share_dir = {0}'.format(share_dir))

                # we copy everything for a full ICU package
                self.copy("*", dst="bin", src=bin_dir, keep_path=True, symlinks=True)
                self.copy("*", dst="include", src=include_dir, keep_path=True, symlinks=True)
                self.copy("*", dst="lib", src=lib_dir, keep_path=True, symlinks=True)
                self.copy("*", dst="share", src=share_dir, keep_path=True, symlinks=True)

            else:
                bin_dir, lib_dir = ('bin64', 'lib64') if self.settings.arch == 'x86_64' else ('bin', 'lib')
                include_dir, bin_dir, lib_dir = (os.path.join(self.name, path) for path in
                                                 ('include', bin_dir, lib_dir))
                self.output.info('include_dir = {0}'.format(include_dir))
                self.output.info('bin_dir = {0}'.format(bin_dir))
                self.output.info('lib_dir = {0}'.format(lib_dir))
                self.copy(pattern='*.h', dst='include', src=include_dir, keep_path=True)
                self.copy(pattern='*.lib', dst='lib', src=lib_dir, keep_path=False)
                self.copy(pattern='*.exp', dst='lib', src=lib_dir, keep_path=False)
                self.copy(pattern='*.dll', dst='lib', src=bin_dir, keep_path=False)
        else:
            bin_dir, include_dir, lib_dir, share_dir = (os.path.join('output', path) for path in
                                                        ('bin', 'include', 'lib', 'share'))
            self.output.info('bin_dir = {0}'.format(bin_dir))
            self.output.info('include_dir = {0}'.format(include_dir))
            self.output.info('lib_dir = {0}'.format(lib_dir))
            self.output.info('share_dir = {0}'.format(share_dir))

            # we copy everything for a full ICU package
            self.copy("*", dst="bin", src=bin_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="include", src=include_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="lib", src=lib_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="share", src=share_dir, keep_path=True, symlinks=True)

    def package_info(self):
        self.cpp_info.libs = []
        vtag = self.version.split('.')[0]
        keep = False
        for lib in tools.collect_libs(self):
            if not vtag in lib:
                self.output.info("OUTPUT LIBRARY: " + lib)
                if lib != 'icudata':
                    self.cpp_info.libs.append(lib)
                else:
                    keep = True

        # if icudata is not last, it fails to build (is that true?)
        if keep:
            self.cpp_info.libs.append('icudata')

        self.env_info.path.append(os.path.join(self.package_folder, "bin"))

        if not self.options.shared:
            self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION")

            if self.settings.os == 'Linux':
                self.cpp_info.libs.append('dl')
