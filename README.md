[Getting Started](#getting-started) |
[Upgrade](#upgrade) |
[Releases](#releases) |
[Roadmap](#roadmap) |
[Status](#status)

**For the Annotation Viewer or the integration with the [OpenMinTeD](
https://openminted.eu) platform, please refer to this [branch](
https://github.com/BlueBrain/neurocurator/blob/annotation_viewer/ANNOTATION_VIEWER.md).**

# NeuroCurator

Desktop application to perform systematic and collaborative curation of
neuroscientific literature.

This is a Graphical User Interface (GUI) for the Python module
[NeuroAnnotation Toolbox (NAT)](https://github.com/BlueBrain/nat).

This framework has been described in details in the following open-access
paper: https://doi.org/10.3389/fninf.2017.00027.

With NeuroCurator, annotations are:
- traceable,
- reusable across projects,
- structured with controlled vocabularies.

---

## Getting Started

### Installation

After having **installed the [requirements](#requirements)**:

```bash
pip3 install neurocurator
```

**Before**, you might want to create a dedicated environment with `conda`:

```bash
conda create --name neurocurator_env python=3.7
conda activate neurocurator_env
```

To launch NeuroCurator:

```bash
neurocurator
```

#### Requirements

  - [Python 3.5+](https://www.python.org/downloads/)
  - [Git 1.7.0+](https://git-scm.com/downloads) (NAT)
  - [ImageMagick **6**](http://docs.wand-py.org/en/latest/guide/install.html) (Wand)
  - [Miniconda](https://conda.io/miniconda.html) (optional)

#### Python dependencies

  - [NAT](https://pypi.org/project/nat/)
  - [PyQt5](https://pypi.org/project/PyQt5/)
  - [NumPy](https://pypi.org/project/numpy/)
  - [pandas](https://pypi.org/project/pandas/)
  - [Wand](https://pypi.org/project/Wand/)

## Upgrade

```bash
pip3 install --upgrade neurocurator
```

If you have used `conda`, activate the environment before:

```bash
conda activate neurocurator_env
```

## Releases

Versions and their notable changes are listed in the [releases section](
https://github.com/BlueBrain/neurocurator/releases/).

## Roadmap

**Ongoing**

1. Stabilize NeuroCurator and NAT (Software Architecture).
2. Split NAT into nat-core, nat-analytics and nat-server (separation of scope).

**TODO**

1. Integrate fully the [Annotation Viewer](
https://github.com/BlueBrain/neurocurator/blob/annotation_viewer/ANNOTATION_VIEWER.md)
into NeuroCurator.
2. Semi-automate the Knowledge Extraction process.

**Done** (latest first)

* Make the annotations publishable into a [Blue Brain Nexus](
https://bluebrain.github.io/nexus/) instance.
* Remove legacy dependencies in NeuroCurator (Qt 4 and Python 3.4).
* Integrate OpenMinTeD annotations into the literature curation framework.
* Visualize NeuroCurator and OpenMinTeD annotations directly on PDFs.
* Make NeuroCurator easily installable, especially by scientists.

Updated on 04.10.18.

## Status

Created during 2016.

Ongoing stabilization and reengineering in the branch _refactor-architecture_.

The branch _refactor-architecture_ is **not** intended to be used by end-users.

New features, bug fixes and improvements are done on the reengineered code sections.

When a reengineered code section is stable, it's merged into the branch
_master_ and a release is published.
