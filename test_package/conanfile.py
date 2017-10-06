from conans import ConanFile, tools, CMake
import os

# conan test_package msys/icu -k -t --build=never -o icu:msvc_platform=msys -o icu:with_data=True -e MSYS_ROOT=D:\dev\msys64

class ICUTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    options = {"with_io": [True, False],
               "with_data": [True, False],
               "shared": [True, False],
               "msvc_platform": ["visual_studio", "cygwin", "msys"],
               "data_packaging": ["shared", "static", "files", "archive"],
               "with_unit_tests": [True, False]}

    default_options = "with_io=False", \
                      "with_data=False", \
                      "shared=True", \
                      "msvc_platform=visual_studio", \
                      "data_packaging=archive", \
                      "with_unit_tests=False"

    def build(self):
        cmake = CMake(self)
        cmake.verbose = True
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*.dll", dst="bin", src="lib")
        self.copy("*.dylib*", dst="bin", src="lib")
        self.copy('*.so*', dst='bin', src='lib')

    def test(self):
        bin_dir = os.path.join(os.getcwd(), "bin")
        os.chdir(bin_dir)
        with tools.environment_append({"LD_LIBRARY_PATH": bin_dir, "DYLD_LIBRARY_PATH": bin_dir}):
            self.run(".{0}test_package".format(os.sep))
