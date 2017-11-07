.. _install:

Installation of PyEcore
========================

This part of the documentation covers the installation of PyEcore.

Using pip
---------

To install PyEcore, simply run this simple command in your terminal of choice::

    $ pip install pyecore


From the Source Code
--------------------

Requests is actively developed on `Github <https://github.com/pyecore/pyecore>`_.

You can either clone the public repository::

    $ git clone git://github.com/pyecore/pyecore.git

Or, download the `tarball <https://github.com/pyecore/pyecore/tarball/master>`_::

    $ curl -OL https://github.com/pyecore/pyecore/tarball/master
    # optionally, zipball is also available (for Windows users).

Once you have a copy of the source, you can embed it in your own Python
package, or install it into your site-packages easily::

    $ cd pyecore
    $ pip install .


Dependencies
------------

The dependencies required by pyecore are:

* ordered-set which is used for the ``ordered`` and ``unique`` collections
  expressed in the metamodel,
* lxml which is used for the XMI parsing.

These dependencies are directly installed if you choose to use ``pip``.
