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

    def source(self):
        tools.get("{0}.zip".format(self.source_url))

    def build(self):
        if self.settings.os == 'Windows':
            sln_file = os.path.join(self.name, "source","allinone","allinone.sln")
            vcvars_command = tools.vcvars_command(self.settings)
            build_command = tools.build_sln_command(self.settings, sln_file, targets=["i18n"])
            command = "{0} && {1}".format(vcvars_command, build_command)
            self.run(command)
        else:
            root_path = self.conanfile_directory.replace('\\', '/')
            platform = ''
            if self.settings.os == 'Linux':
                platform = 'Linux'
            elif self.settings.os == 'MacOs':
                platform = 'MacOSX'
            self.run("bash {0}/build_icu_{1}.sh {0} {2} {0}/install_{3}").format(root_path,self.settings.build_type,platform,self.settings.build_type)

    def package(self):
        install_path = "install_{0}".format(self.settings.build_type)
        self.copy("*", "include", "{0}/include".format(install_path), keep_path=True)

        self.copy("*.exe", "bin", "{0}/bin".format(install_path), keep_path=False)
        self.copy("*.lib", "lib", "{0}/lib".format(install_path), keep_path=False)
        self.copy("*.pdb", "lib", "build_{0}/lib".format(self.settings.build_type), keep_path=False)
        self.copy("*.pdb", "lib", "build_{0}/tools/toolutil".format(self.settings.build_type), keep_path=False)
        self.copy("*.dll", "bin", "{0}/bin".format(install_path), keep_path=False)
        self.copy("*.pdb", "bin", "{0}/lib".format(install_path), keep_path=False)

        self.copy("*.dat", "data", "{0}/share".format(install_path), keep_path=False)

        if self.settings.build_type == 'Debug':
            self.copy("*.cpp", "src", "icu", keep_path=True)
            self.copy("*.hpp", "src", "icu", keep_path=True)
            self.copy("*.h", "src", "icu", keep_path=True)
            self.copy("*.c", "src", "icu", keep_path=True)

    def package_info(self):
        self.cpp_info.defines = ['U_STATIC_IMPLEMENTATION=1', 'U_CHARSET_IS_UTF8=1', 'UNISTR_FROM_CHAR_EXPLICIT=explicit', 'UNISTR_FROM_STRING_EXPLICIT=explicit', 'U_NO_DEFAULT_INCLUDE_UTF_HEADERS=1']
        if self.settings.compiler == 'Visual Studio':
            if self.settings.build_type == 'Debug':
                self.cpp_info.libs = ["sicuucd", "sicuind", "sicudtd", 'Advapi32']
            elif self.settings.build_type == 'Release':
                self.cpp_info.libs = ["sicuuc", "sicuin", "sicudt", 'Advapi32']
