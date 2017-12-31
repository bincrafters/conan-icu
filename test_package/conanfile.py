from conans import ConanFile, tools, CMake
import os

class ICUTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        lib_dir_src = 'lib64' if self.settings.arch == 'x86_64' and self.settings.os == 'Windows' else 'lib'
        self.copy("*.dll", dst="bin", src=lib_dir_src)
        self.copy("*.dylib*", dst="bin", src=lib_dir_src)
        self.copy('*.so*', dst='bin', src=lib_dir_src)

    def test(self):
        bin_dir = os.path.join(os.getcwd(), "bin")
        os.chdir(bin_dir)
        with tools.environment_append({"LD_LIBRARY_PATH": bin_dir, "DYLD_LIBRARY_PATH": bin_dir}):
            self.run(".{0}test_package".format(os.sep))

