from conans import ConanFile, CMake, tools
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        
    def imports(self):
        self.copy("*", dst="bin", src="bin")
        self.copy("*", dst="bin", src="lib")

    def test(self):
        bin_dir = os.path.join(os.getcwd(), "bin")
        os.chdir(bin_dir)
        with tools.environment_append({"LD_LIBRARY_PATH": bin_dir}):
            self.run(".{0}test_package".format(os.sep))