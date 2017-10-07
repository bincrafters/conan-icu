from conan.packager import ConanMultiPackager, os, sys, re
from distutils.util import strtobool

from collections import defaultdict

if __name__ == "__main__":
    conan_build_options = {}
    conan_build_settings = {}

    reponame_a = os.getenv("APPVEYOR_REPO_NAME","")
    repobranch_a = os.getenv("APPVEYOR_REPO_BRANCH","")

    reponame_t = os.getenv("TRAVIS_REPO_SLUG","")
    repobranch_t = os.getenv("TRAVIS_BRANCH","")

    username, repo = reponame_a.split("/") if reponame_a else reponame_t.split("/")
    channel, version = repobranch_a.split("/") if repobranch_a else repobranch_t.split("/")

    with open("conanfile.py", "r") as conanfile:
        contents = conanfile.read()
        name = re.search(r'name\s*=\s*"(\S*)"', contents).groups()[0]

    os.environ["CONAN_USERNAME"] = username
    os.environ["CONAN_CHANNEL"] = channel
    os.environ["CONAN_REFERENCE"] = "{0}/{1}".format(name, version)
    os.environ["CONAN_UPLOAD"]="https://api.bintray.com/conan/{0}/public-conan".format(username)
    os.environ["CONAN_REMOTES"]="https://api.bintray.com/conan/conan-community/conan"

    builder = ConanMultiPackager(args="--build missing")

    if "CONAN_ICU_SHARED" in os.environ:
        conan_build_options.update({"icu:shared": True if strtobool(os.environ["CONAN_ICU_SHARED"]) else False})

    #if "CONAN_ICU_WITH_DATA" in os.environ:
    conan_build_options.update({"icu:with_data": True})

    if "CONAN_ICU_DATA_PACKAGING" in os.environ:
        conan_build_options.update({"icu:data_packaging": os.environ["CONAN_ICU_DATA_PACKAGING"]})


    if 'TRAVIS_OS_NAME' not in os.environ:
        if "CONAN_ICU_MSVC_PLATFORM" in os.environ:
            conan_build_options.update({"icu:msvc_platform": os.environ["CONAN_ICU_MSVC_PLATFORM"]})
    else:
        if os.environ['TRAVIS_OS_NAME'] == 'linux':
            conan_build_settings.update({"icu:os": "Linux"})
        if os.environ['TRAVIS_OS_NAME'] == 'osx':
            conan_build_settings.update({"icu:os": "Macos"})

    builder.add(settings=conan_build_settings, options=conan_build_options)

    builder.run()
