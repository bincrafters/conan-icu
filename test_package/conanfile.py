from conans import ConanFile, CMake, tools
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure(source_dir=self.conanfile_directory, build_dir="./")
        cmake.build()
        
    def imports(self):
        self.copy("*", dst="bin", src="bin")
        self.copy("*", dst="bin", src="lib")
        self.copy("libicudata*", dst="lib", src="lib")
        
    def test(self):
        os.chdir("bin")
        self.run("test_package")