[Getting Started](#getting-started) |
[Upgrade](#upgrade) |
[Releases](#releases) |
[Status](#status)

**For the Annotation Viewer or the integration with the
[OpenMinTeD](https://openminted.eu)
platform, please refer to this
[branch](https://github.com/BlueBrain/neurocurator/blob/annotation_viewer/ANNOTATION_VIEWER.md).**

# NeuroCurator

Desktop application to perform systematic and collaborative curation of
neuroscientific literature.

This is a Graphical User Interface (GUI) for the Python package
[NeuroAnnotation Toolbox (NAT)](https://github.com/BlueBrain/nat).

This framework has been described in details in the following open-access
paper: https://doi.org/10.3389/fninf.2017.00027.

With NeuroCurator, annotations are:
- traceable,
- reusable across projects,
- structured with controlled vocabularies.

---

## Getting Started

### Requirements:

System side:

- [Git 1.7.0+](https://git-scm.com/downloads)
- [ImageMagick 6](http://docs.wand-py.org/en/latest/guide/install.html)
- [Python 3.4*](https://www.python.org/downloads/)
- [Qt 4.8.7*](https://doc.qt.io/archives/qt-4.8/supported-platforms.html)
- [Miniconda*](https://conda.io/miniconda.html)

Python side:

- [NAT](https://github.com/BlueBrain/nat)
- [PySide 1.2.4](https://wiki.qt.io/PySide)
- [NumPy](http://www.numpy.org)
- [pandas](https://pandas.pydata.org)
- [Wand](http://docs.wand-py.org)

*Miniconda is not required. It simplifies only temporary the installation:
no need to compile Qt and to install manually Python 3.4. It also makes the
installation easier on Windows (pandas).

### Installation:

Instructions for macOS 10.13+, Ubuntu 16.04+, Windows 10+.

**1 - Create a virtual environment with Python 3.4:**
```bash
conda create -y --name nc python=3.4
```

**2 - Switch to the virtual environment:**

On macOS and Linux:
```bash
source activate nc
```

On Windows:
```bash
activate nc
```

**3 -  Install PySide 1.2.4 and Qt 4.8.7 from [conda-forge](https://conda-forge.org):**
```bash
conda install -y pyside --channel conda-forge
```

**4 - Install NAT:**

On macOS and Linux:
```bash
pip install nat
```

On Windows:
```bash
conda install -y pandas
pip install beautifulsoup4 gitpython lxml numpy parse pyzotero quantities scipy wand
pip install nat --no-deps
```

**5 - Install NeuroCurator:**
```bash
pip install neurocurator --no-deps
```

### Use

Launch NeuroCurator:
```bash
neurocurator
```

For the future uses:
1. enter the virtual environment: `source activate nc` or  `activate nc`
2. launch NeuroCurator: `neurocurator`
3. use NeuroCurator
4. close NeuroCurator
5. exit the virtual environment: `source deactivate` or `deactivate`

## Upgrade

Instructions for macOS 10.13+, Ubuntu 16.04+, Windows 10+.

**1 - Switch to the virtual environment:**

On macOS and Linux:
```bash
source activate nc
```

On Windows:
```bash
activate nc
```

**2 - Upgrade NAT:**

```bash
pip install --upgrade nat
```

**3 - Upgrade NeuroCurator:**

```bash
pip install --upgrade neurocurator --no-deps
```

## Releases

Versions and their notable changes are listed in the
[releases section](https://github.com/BlueBrain/neurocurator/releases/).

## Status

Created during 2016.

Ongoing stabilization and reengineering in the branch _refactor-architecture_.

The branch _refactor-architecture_ is **not** intended to be used by end-users.

New features, bug fixes and improvements are done on the reengineered code sections.

When a reengineered code section is stable, it's merged into the branch
_master_ and a release is published.
