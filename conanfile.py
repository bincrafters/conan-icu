from conans import ConanFile, VisualStudioBuildEnvironment, tools
import os, glob

class IcuConan(ConanFile):
    name = "icu"
    version = "59.1"
    license="http://www.unicode.org/copyright.html#License"
    description = 'ICU is a mature, widely used set of C/C++ and Java libraries providing Unicode and Globalization support for software applications.'
    url = "https://github.com/bincrafters/conan-icu"
    settings = "os", "arch", "compiler", "build_type"
    source_url = "http://download.icu-project.org/files/icu4c/{0}/icu4c-{1}-src".format(version,version.replace('.', '_'))

    def source(self):
        if self.settings.os == 'Windows':
            tools.get("{0}.zip".format(self.source_url))
        else:
            tools.get("{0}.tgz".format(self.source_url))

    def build(self):
        root_path = self.conanfile_directory.replace('\\', '/')
        src_path = os.path.join(root_path, self.name, 'source')
        if self.settings.os == 'Windows':
            sln_file = os.path.join(src_path,"allinone","allinone.sln")
            vcvars_command = tools.vcvars_command(self.settings)
            build_command = tools.build_sln_command(self.settings, sln_file, targets=["i18n"])
            command = "{0} && {1}".format(vcvars_command, build_command)
            self.run(command)
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
        install_path = "output"
        self.copy("*", "include", "{0}/include".format(install_path), keep_path=True)
        self.copy("*icui18n.dll", "lib", "{0}/lib".format(install_path), keep_path=False)
        self.copy("*icui18n.dylib", "lib", "{0}/lib".format(install_path), keep_path=False)
        self.copy("*icui18n.so", "lib", "{0}/lib".format(install_path), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = self.collect_libs()
