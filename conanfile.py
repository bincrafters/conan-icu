from conans import ConanFile, tools
import os

class IcuConan(ConanFile):
    name = "icu"
    version = "59.1"
    license="http://www.unicode.org/copyright.html#License"
    description = 'ICU is a mature, widely used set of C/C++ and Java libraries providing Unicode and Globalization support for software applications.'
    url = "https://github.com/bincrafters/conan-icu"
    settings = "os", "arch", "compiler", "build_type"
    source_url = "http://download.icu-project.org/files/icu4c/{0}/icu4c-{1}-src".format(version,version.replace('.', '_'))
    options = {"with_io": [True, False]}
    default_options = "with_io=False"

    def source(self):
        if self.settings.os == 'Windows':
            tools.get("{0}.zip".format(self.source_url))
        else:
            tools.get("{0}.tgz".format(self.source_url))

    def build(self):
        root_path = self.conanfile_directory
        tools.replace_in_file(
            os.path.join(root_path, self.name,'source','data','makedata.mak'),
            r'GODATA "$(ICU_LIB_TARGET)" "$(TESTDATAOUT)\testdata.dat"',
            r'GODATA "$(ICU_LIB_TARGET)"')
        src_path = os.path.join(root_path, self.name, 'source')
        if self.settings.os == 'Windows':
            sln_file = os.path.join(src_path,"allinone","allinone.sln")
            vcvars_command = tools.vcvars_command(self.settings)
            targets = ["i18n","common","pkgdata"]
            if self.options.with_io:
                targets.append('io')
            build_command = tools.build_sln_command(self.settings, sln_file, targets=targets, upgrade_project=False)
            build_command = build_command.replace('"x86"','"Win32"')
            command = "{0} && {1}".format(vcvars_command, build_command)
            self.run(command)
            cfg = 'x64' if self.settings.arch == 'x86_64' else 'x86'
            cfg += "\\"+str(self.settings.build_type)
            data_dir = src_path+"\\data"
            bin_dir = data_dir+"\\..\\..\\bin"
            if self.settings.arch == 'x86_64':
                bin_dir += '64'
            makedata = '{vcvars} && cd {datadir} && nmake /a /f makedata.mak ICUMAKE="{datadir}" CFG={cfg}'.format(
                vcvars=vcvars_command,
                datadir=data_dir,
                cfg=cfg)
            self.output.info(makedata)
            self.run(makedata)
        else:
            platform = ''
            if self.settings.os == 'Linux':
                if self.settings.compiler == 'gcc':
                    platform = 'Linux/gcc'
                else:
                    platform = 'Linux'
            elif self.settings.os == 'Macos':
                platform = 'MacOSX'
            enable_debug = ''
            if self.settings.build_type == 'Debug':
                enable_debug = '--enable-debug'
            self.run("cd {0} && bash runConfigureICU {1} {2} --prefix={3}".format(
                src_path, enable_debug, platform, os.path.join(root_path,'output')))
            self.run("cd {0} && make install".format(src_path))

    def package(self):
        if self.settings.os == 'Windows':
            self.copy("*", "include", os.path.join(self.name,"include"), keep_path=True)
            libs = ['in', 'uc', 'dt']
            if self.options.with_io:
                libs.append('io')
            bin_dir = 'bin'
            lib_dir = 'lib'
            if self.settings.arch == 'x86_64':
                bin_dir = 'bin64'
                lib_dir = 'lib64'
            bin_dir = os.path.join(self.name, bin_dir)
            lib_dir = os.path.join(self.name, lib_dir)
            self.output.info("BIN_DIR = {0}".format(bin_dir))
            self.output.info("LIB_DIR = {0}".format(lib_dir))
            for lib in libs:
                self.copy(pattern="*icu{0}*.dll".format(lib), dst="lib", src=bin_dir, keep_path=False)
                self.copy(pattern="*icu{0}*.exp".format(lib), dst="lib", src=lib_dir, keep_path=False)
                self.copy(pattern="*icu{0}*.lib".format(lib), dst="lib", src=lib_dir, keep_path=False)
        else:
            with tools.chdir(os.path.join(self.build_folder , "output", "include")):
                self.copy(pattern="*", dst="include", keep_path=True)
            with tools.chdir(os.path.join(self.build_folder , "output", "lib")):
                self.copy(pattern="*.dylib*", dst="lib", keep_path=True, symlinks=True)
                self.copy(pattern="*.so*", dst="lib", keep_path=False, symlinks=True)

    def package_info(self):
        self.cpp_info.libs = self.collect_libs()
        self.env_info.path = [os.path.join(self.package_folder, "lib")] + self.env_info.path
