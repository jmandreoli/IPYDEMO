# IPYDEMO

This package contains various IPython demos based on Jupyter notebooks.

## Installation

Download the zip archive and expand it in some folder on your machine. There are dependencies to numpy, scipy, matplotlib (recent versions). If you want the documentation of the package, go to folder ``doc``, copy file ``Makefile-in`` into ``Makefile`` and configure the latter, then run ``make``.

## Execution of the demos

The demos are given as jupyter notebooks in folder ``demo``. Most use matplotlib animations, and are configured with the `nbagg` backend which displays the animations inline. For better performances, it is advised to use the default backend instead. Don't use the `inline` backend as it does not support animations. To change the backend in a demo, modify the first line to be one of the following:

    %pylab
    %pylab nbagg

These demos assume that this package is visible in the `PYTHONPATH` environment variable. If that is not the case, just add the following at the beginning of each demo:

    import sys; sys.path.insert(0,r'/your/path/to/this/package')
