# IPYDEMO

This package contains various IPython demos based on Jupyter notebooks. The purpose is to illustrate their capabilities. Currently available:

* simulation of various dynamical systems defined by ordinary differential equations (sub-package `odesimu`)
* multi-zoom exploration of fractals (sub-package `fractals`)
* exploration of polyhedra (sub-package `polyhedra`)
* exploration of Sudoku problem space (sub-package `sudoku`)

## Dependencies

* Requires [Python 3](https://www.python.org). There are dependencies to [numpy, scipy](https://www.scipy.org), [matplotlib](http://matplotlib.org) (recent versions). There exist all-in-one software packages which simplify the management of these requirements: [Miniconda](https://www.continuum.io), [Python(x,y)](http://python-xy.github.io).
* A [Jupyter](http://jupyter.org) server capable of launching a Python 3 kernel should be up and running, or the standalone Jupyter lab desktop client.

That should be pretty all. Should work on both Linux, MacOS and Windows.

## Installation

Download the zip archive and expand it in some folder on your machine, e.g. your `Download` folder. Then create a symbolic link to the path `~/Download/IPYDEMO/src` with name `ipyshow` (the name used in the demos) somewhere among the `sys.path` of your python install (e.g. by including it in the `PYTHONPATH` environment variable).

## Execution of the demos

The demos are given as jupyter notebooks in folder `ipyshow/demo`. Most use matplotlib animations, and are configured with the `widget` backend which displays the animations inline. For better performances, it is advised to use the `qt5` backend or similar (rendering in a separate window). Don't use the `inline` backend since, although it is inline, it does not support animations. To change the backend in a demo, modify the first line to be one of the following (and restart the kernel):

    %matplotlib qt5

## Write your own demos...

You can use sub-packages `odesimu` and `fractals` to build your own demos (don't hesitate to contact me on github if you have nice demos to add). The documentation of these modules can be generated using [Sphinx](http://www.sphinx-doc.org): go to folder `doc`, copy file `Makefile-in` into `Makefile` and configure the latter (instructions inside), then run `make html` (or `make pdf` etc.).
