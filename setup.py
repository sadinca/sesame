#!/usr/bin/env python
 
import sys
import configparser
from setuptools import setup, Extension
from distutils.command.build_ext import build_ext
from distutils.errors import DistutilsPlatformError, DistutilsExecError, CCompilerError


CONFIG_FILE = 'setup.cfg'

ext_modules = [Extension('mumps._dmumps', sources=['mumps/_dmumps.c'])]

ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)


class BuildFailed(Exception):
    def __init__(self):
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(sys.exc_info()[1]): # works with both py 2/3
                raise BuildFailed()
            raise

cmdclass = {'build_ext': ve_build_ext}



def status_msgs(*msgs):
    print('=' * 75)
    for msg in msgs:
        print(msg)
    print('=' * 75)



def run_setup(packages, ext_modules):
    setup(
        name = 'sesame',
        version = '0.1',
        author = 'Benoit H. Gaury',
        author_email = 'benoit.gaury@nist.gov',
        packages = packages,
        cmdclass = cmdclass,
        ext_modules = ext_modules,
        classifiers = [
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 3',
        ],
    )


config = configparser.ConfigParser()
try:
    with open(CONFIG_FILE) as f:
        config.readfp(f)
except IOError:
    print("Could not open config file.")


if 'mumps' in config.sections():
    kwrds = {}
    for name, value in config.items('mumps'):
        kwrds[name] = value

    ext_modules = [Extension(
        'sesame.mumps._dmumps',
        sources=['sesame/mumps/_dmumps.c'],  
        libraries=[kwrds['libraries']],
        library_dirs=[kwrds['library_dirs']],
        include_dirs=[kwrds['include_dirs']])]

    packages = ['sesame', 'sesame.mumps']

    try:
        run_setup(packages, ext_modules)
        status_msgs(
            "Build summary: Build successful.")
    except BuildFailed as exc:
        status_msgs(
            exc.cause,
            "WARNING: The MUMPS extension could not be compiled. " +
            "Retrying the build without the MUMPS extension now.")
        run_setup(['sesame'], [])
        status_msgs(
            "Build summary: The MUMPS extension could not be compiled. " +  
            "Plain-Python build succeeded.")
else:
    run_setup(['sesame'], [])
    status_msgs( "Build summary: Plain-Python build succeeded.")