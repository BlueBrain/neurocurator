__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

import os

from setuptools import setup

NEUROCURATOR_VERSION = "0.4.3"
NAT_MINIMUM_VERSION = "0.4.2"

HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file.
# Convert to rst with: pandoc --from=markdown --to=rst README.md -o README.rst.
with open(os.path.join(HERE, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="neurocurator",
    version=NEUROCURATOR_VERSION,
    description="Application to perform curation of neuroscientific literature.",
    long_description=long_description,
    keywords="neuroscience annotation curation literature modeling parameters",
    url="https://github.com/BlueBrain/neurocurator",
    author="Christian O'Reilly, Pierre-Alexandre Fonta",
    author_email="christian.oreilly@epfl.ch, pierre-alexandre.fonta@epfl.ch",
    # NB: 'If maintainer is provided, distutils lists it as the author in PKG-INFO'.
    # https://docs.python.org/3/distutils/setupscript.html#meta-data
    # maintainer="Pierre-Alexandre Fonta",
    # maintainer_email="pierre-alexandre@epfl.ch",
    license="GPLv3",
    packages=["neurocurator"],
    python_requires="~=3.4.0",  # Until #6 is solved.
    install_requires=[
        "nat>=" + NAT_MINIMUM_VERSION,
        "pyside",
        "numpy",
        "pandas",
        "wand"
    ],
    data_files=[("", ["LICENSE.txt"])],
    entry_points={
        # NB: gui_scripts: on Windows no console is attached (no stdout/stderr).
        "console_scripts": ["neurocurator = neurocurator.__main__:main"]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Environment :: X11 Applications :: Qt",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: Free for non-commercial use",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.4",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English"
    ]
)
