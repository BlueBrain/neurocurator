# neurocurator

GUI-based application and API to perform systematic and collaborative scientific literature curation. This is a front-end for the NeuroAnnotation Toolbox (NAT).

This framework has been described in details in the following open-access paper: http://journal.frontiersin.org/article/10.3389/fninf.2017.00027/full 

# Installation

## macOS standalone executable

**EXPERIMENTAL**

Latest NeuroCurator version (10/10/17) from *master* packaged on an up-to-date El Capitan (10.11.6).

Launched successfully on El Capitan (10.11.6) and Sierra (10.12.6). It should also work on High Sierra (10.13.x).

The executable can be downloaded here: https://goo.gl/TmFJH3.

It requires [Git](https://git-scm.com) and [ImageMagick](https://www.imagemagick.org) 6.

ImageMagick 6 can be installed with [Homebrew](https://brew.sh):
```
brew install imagemagick@6
brew link imagemagick@6 --force
```

Git can also be installed with Homebrew:
```
brew install git
```

To launch NeuroCurator, in the folder where you downloaded the file:
```
./NeuroCurator_mac_10.11.6_x64
```

You might require to allow execution:
```
sudo chmod u+x NeuroCurator_mac_10.11.6_x64
```

A *settings.ini* file will be created in the same folder. It holds the configuration of NeuroCurator.
