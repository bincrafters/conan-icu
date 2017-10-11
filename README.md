[ ![Download](https://api.bintray.com/packages/bincrafters/public-conan/icu%3Abincrafters/images/download.svg?version=59.1%3Astable) ](https://bintray.com/bincrafters/public-conan/icu%3Abincrafters/59.1%3Astable/link)
[![Build Status](https://travis-ci.org/bincrafters/conan-icu.svg?branch=stable%2F59.1)](https://travis-ci.org/bincrafters/conan-icu)
[![Build status](https://ci.appveyor.com/api/projects/status/axdtbjsbh6cja93i?svg=true)](https://ci.appveyor.com/project/BinCrafters/conan-icu)

## This repository holds a conan recipe for IBM ICU.

[Conan.io](https://conan.io) package for [IBM ICU](http://icu-project.org) project

The packages generated with this **conanfile** can be found in [Bintray](https://bintray.com/bincrafters/public-conan/ICU%3Abincrafters).

## For Users: Use this package

### Basic setup

    $ conan install icu/59.1@bincrafters/testing

### Project setup

If you handle multiple dependencies in your project is better to add a *conanfile.txt*

    [requires]
    icu/59.1@bincrafters/stable

    [generators]
    txt

Complete the installation of requirements for your project running:

    $ mkdir build && cd build && conan install ..

Note: It is recommended that you run conan install from a build directory and not the root of the project directory.  This is because conan generates *conanbuildinfo* files specific to a single build configuration which by default comes from an autodetected default profile located in ~/.conan/profiles/default .  If you pass different build configuration options to conan install, it will generate different *conanbuildinfo* files.  Thus, they shoudl not be added to the root of the project, nor committed to git.

### Package Options

This package has the following options: 

|Option Name		 | Default Values   | Possible Value                      | Description
|---------------------|-------------------|----------------------------------------------------------
|shared					 | True                  | True/False                            | Use as a shared library or static library
|with_io				 | False                 | True/False                            | Compile the ICU Ustdio/iostream library
|with_unit_tests	 | False                 | True/False                            | Run the ICU unit tests before compiling
|with_data			 | False                 | True/False                            | Build the ICU sample data with default settings. 
|with_msys			 | False                 | True/False                            | Supplies the MSYS Conan package to use at build time
|msvc_platform	 | visual_studio     | visual_studio, cygwin, msys  | Choose an alternate compiler front-end
|data_packaging	 | archive             | shared, static, files, archive   | See [ICU Data Packaging documentation](http://userguide.icu-project.org/packaging)

## For Packagers: Publish this Package

The example below shows the commands used to publish to bincrafters conan repository. To publish to your own conan respository (for example, after forking this git repository), you will need to change the commands below accordingly.

## Build  

This is a header only library, so nothing needs to be built.

## Package

    $ conan create bincrafters/testing

## Add Remote

	$ conan remote add bincrafters "https://api.bintray.com/conan/bincrafters/public-conan"

## Upload

    $ conan upload ICU/59.1@bincrafters/stable --all -r bincrafters

### License
[MIT](LICENSE)
