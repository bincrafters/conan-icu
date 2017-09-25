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
        self.copy("libicudata*", dst="lib", src="lib")
        
    def test(self):
        self.run("ls -l")
        self.run('find . -name "*"')
        bin_dir = os.path.join(os.getcwd(), "bin")
        lib_dir = os.path.join(os.getcwd(), "lib")
        with tools.environment_append({"DYLD_LIBRARY_PATH": lib_dir}):
            self.run(os.path.join("bin","test_package"))