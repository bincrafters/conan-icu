from conans import ConanFile, VisualStudioBuildEnvironment, tools
import os, glob

class IcuConan(ConanFile):
    name = "icu"
    version = "59.1"
    license="http://www.unicode.org/copyright.html#License"
    description = 'ICU is a mature, widely used set of C/C++ and Java libraries providing Unicode and Globalization support for software applications.'
    url = "https://bitbucket.org/birconan/conan/issues"
    settings = "os", "arch", "compiler", "build_type"
    generators = []
    exports = 'build_icu_Debug.sh','build_icu_Release.sh'
    
    source_url = f"http://download.icu-project.org/files/icu4c/{version}/icu4c-{version.replace('.', '_')}-src"

    def source(self):
        ext = 'tgz'
        tools.download(f'{self.source_url}.{ext}', f'icu.{ext}')
        tools.unzip(f'icu.{ext}')
        os.unlink(f'icu.{ext}')

    def build(self):
            
        platform = ''
        if self.settings.os == 'Windows':
            platform = 'Cygwin/MSVC'
        elif self.settings.os == 'Linux':
            platform = 'Linux'
        elif self.settings.os == 'MacOs':
            platform = 'MacOSX'

        root_path = self.conanfile_directory.replace('\\', '/')

        cmd = 'bash'
        if self.settings.os == 'Windows':
            suffix = ''
            if self.settings.build_type == 'Debug':
                suffix = 'd'
            tools.replace_in_file('icu/source/tools/toolutil/Makefile.in', '$(LIBCPPFLAGS)', f'$(LIBCPPFLAGS) -Fdsicutu{suffix}.pdb')
            tools.replace_in_file('icu/source/runConfigureICU', '-Gy -MD', '-Zi -Gy -MD')
            tools.replace_in_file('icu/source/runConfigureICU', 'DEBUG_LDFLAGS=\'-DEBUG\'', 'DEBUG_LDFLAGS=\'-DEBUG\'\nRELEASE_LDFLAGS=\'-DEBUG\'')
            cmd = 'C:/devel/cygwin/bin/bash -l -i'
        self.run(f'{cmd} {root_path}/build_icu_{self.settings.build_type}.sh {root_path} {platform} {root_path}/install_{self.settings.build_type}')

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
