# IPYDEMO

This package proposes various IPython demos based on Jupyter notebooks.

The demos are in folder ``demo``. They can be run inside the browser with the nbagg backend, but for better performances, it is advised to use the default backend. Don't use the inline backend as it does not support animations. To change the backend in a demo, modify the first line to be one of the following:

    %pylab
    %pylab nbagg

These demos assume that this package is visible in the PYTHONPATH. If that is not the case, just add the following at the beginning of each demo:

    import sys; sys.insert(0,'/full/path/to/this/package')
