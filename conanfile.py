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
        tools.get("{0}.zip".format(self.source_url))

    def build(self):
        if self.settings.os == 'Windows':
            sln_file = os.path.join(self.name, "source","allinone","allinone.sln")
            vcvars_command = tools.vcvars_command(self.settings)
            build_command = tools.build_sln_command(self.settings, sln_file)
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
        install_path = f'install_{self.settings.build_type}'
        self.copy("*", "include", f"{install_path}/include", keep_path=True)

        self.copy("*.exe", "bin", f"{install_path}/bin", keep_path=False)
        self.copy("*.lib", "lib", f"{install_path}/lib", keep_path=False)
        self.copy("*.pdb", "lib", f"build_{self.settings.build_type}/lib", keep_path=False)
        self.copy("*.pdb", "lib", f"build_{self.settings.build_type}/tools/toolutil", keep_path=False)
        self.copy("*.dll", "bin", f"{install_path}/bin", keep_path=False)
        self.copy("*.pdb", "bin", f"{install_path}/lib", keep_path=False)

        self.copy("*.dat", "data", f"{install_path}/share", keep_path=False)

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
