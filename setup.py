from distutils.core import setup, Extension
import os

PACKAGE = "neurocurator"
NAME = "neurocurator"
DESCRIPTION = "GUI-based application and API to perform systematic and collaborative scientific literature curation."
AUTHOR = "Christian O'Reilly"
AUTHOR_EMAIL = "christian.oreilly@epfl.ch"
VERSION = "0.1.0"

def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )

def find_packages(path, base="" ):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package( dir ):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages

packages=find_packages("..")

setup(
    name=NAME,
    packages=packages.keys(),
    package_dir=packages,
    package_data={NAME: ["additionsToOntologies.csv", "modelingDictionary.csv", "onto/*.dic", "onto/*.tree"]},
    version=VERSION, #data_files=[("", ["additionsToNeurolex.csv"])],
    description=DESCRIPTION,
    long_description=DESCRIPTION, #open("README.txt").read(),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,  
    license='LICENSE.txt',
    requires=['numpy'],
    classifiers=["Development Status :: 3 - Alpha",
			"Environment :: MacOS X", #"Environment :: Win32 (MS Windows)",
			"Environment :: X11 Applications",
			"Intended Audience :: Developers",
			"Intended Audience :: Science/Research",
			"License :: Free for non-commercial use",
			"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
			"Natural Language :: English",
			"Programming Language :: Python :: 3.4",
			"Topic :: Scientific/Engineering"])

	
	
	
	
