# IPYDEMO

This package contains various IPython demos based on Jupyter notebooks. The purpose is to illustrate the capabilities of IPython+Jupyter. Currently available:

* simulation of various dynamic systems defined by ordinary differential equations (sub-package `odesimu`)
* multi-zoom exploration of fractals (sub-package `fractals`)

## Dependencies

* Requires [Python 3](https://www.python.org). There are dependencies to [numpy, scipy](https://www.scipy.org), [matplotlib](http://matplotlib.org) (recent versions). There exist all-in-one software packages which simplify the management of these requirements: [Miniconda](https://www.continuum.io), [Python(x,y)](http://python-xy.github.io).
* A [Jupyter](http://jupyter.org) server capable of launching a Python 3 kernel should be up and running.

That should be pretty all. Should work on both Linux, MacOS and Windows.

## Installation

Download the zip archive and expand it in some folder on your machine. That folder should be included in the `PYTHONPATH` environment variable seen by your Jupyter kernel. Otherwise, just add the following at the beginning of each demo notebook:

    import sys; sys.path.insert(0,r'/your/path/to/this/package')

Rename sub-folder `IPYDEMO` into `ipyshow`, which is the name of the package as used in the demos.

## Execution of the demos

The demos are given as jupyter notebooks in folder `ipyshow/demo`. Most use matplotlib animations, and are configured with the `nbagg` backend which displays the animations inline. For better performances, it is advised to use the default backend instead. Don't use the `inline` backend since, although it is inline, it does not support animations. To change the backend in a demo, modify the first line to be one of the following (and restart the kernel):

    %pylab
    %pylab nbagg

## Write your own demos...

You can use sub-packages `odesimu` and `fractals` to build your own demos (don't hesitate to contact me on github if you have nice demos to add). The documentation of these modules can be generated using [Sphinx](http://www.sphinx-doc.org): go to folder `doc`, copy file `Makefile-in` into `Makefile` and configure the latter (instructions inside), then run `make html` (or `make pdf` etc.).
