[Getting started](#getting-started) |
[Releases](#releases) |
[Status](#status) |
[Requirements: macOS](#macos) |
[Requirements: Ubuntu](#ubuntu) |
[Packaging](#packaging)

# NeuroCurator

Desktop application to perform systematic and collaborative curation of neuroscientific literature.

This is a Graphical User Interface (GUI) for the Python package [NeuroAnnotation Toolbox (NAT)](https://github.com/BlueBrain/nat).

This framework has been described in details in the following open-access paper: https://doi.org/10.3389/fninf.2017.00027.

With NeuroCurator, annotations are:
- traceable,
- reusable across projects,
- structured with controlled vocabularies.

---

## Getting started

Install the [requirements](#requirements).

Download the packaged executable of the [latest release](https://github.com/BlueBrain/neurocurator/releases/latest).

Launch NeuroCurator:
```
./neurocurator_<version>_<operating system>_x64
```
(in the folder where you downloaded the file)

## Releases

In the [dedicated section](https://github.com/BlueBrain/neurocurator/releases/), you can find:
- the latest version,
- the notable changes of each version,
- the packaged executables for macOS and Ubuntu.

## Status

Created during 2016.

Ongoing reengineering in the branch _refactor-architecture_.

The branch _refactor-architecture_ is **not** intended to be used by end-users.

New features, bug fixes and improvements are done on the reengineered code sections.

When a reengineered code section is stable, it's merged into the branch _master_ and a release is published.

## Requirements

### macOS

Work on El Capitan (10.11.x) and higher.

The packaged executable needs [Git](https://git-scm.com) and [ImageMagick](https://www.imagemagick.org) **6**.

ImageMagick 6 can be installed with [Homebrew](https://brew.sh):
```
brew install imagemagick@6
brew link imagemagick@6 --force
```

Git can also be installed with Homebrew:
```
brew install git
```

You might require to allow execution:
```
sudo chmod u+x neurocurator_<version>_mac_x64
```

### Ubuntu

Should work on 16.04.x LTS (Xenial) and higher, and also on other Debian-based distributions.

The packaged executable needs [Git](https://git-scm.com):
```
sudo apt install git
```

## Packaging

The code from the branch _master_ of NeuroCurator and [NAT](https://github.com/BlueBrain/nat) is used.

The packaged executables of NeuroCurator are created on up-to-date 64 bits OS X El Capitan and Ubuntu 16.04 LTS systems.

NeuroCurator's configuration is stored in a *settings.ini* file created alongside the executable.
