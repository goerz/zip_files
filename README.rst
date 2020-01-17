=========
zip-files
=========

.. image:: https://img.shields.io/badge/github-goerz/zip__files-blue.svg
   :alt: Source code on Github
   :target: https://github.com/goerz/zip_files

.. image:: https://img.shields.io/pypi/v/zip_files.svg
   :alt: zip-files on the Python Package Index
   :target: https://pypi.python.org/pypi/zip_files

.. image:: https://img.shields.io/travis/goerz/zip_files.svg
   :alt: Travis Continuous Integration
   :target: https://travis-ci.org/goerz/zip_files

.. image:: https://ci.appveyor.com/api/projects/status/k2lqxw97gv2m9gpm/branch/master?svg=true
   :alt: AppVeyor Continuous Integration
   :target: https://ci.appveyor.com/project/goerz/zip-files

.. image:: https://img.shields.io/coveralls/github/goerz/zip_files/master.svg
   :alt: Coveralls
   :target: https://coveralls.io/github/goerz/zip_files?branch=master

.. image:: https://img.shields.io/badge/License-BSD-green.svg
   :alt: BSD License
   :target: https://opensource.org/licenses/BSD-3-Clause

Command line utilities for creating zip files.

Provides the ``zip-files`` and ``zip-folder`` command line utilities. These are
intended as an easy platform-independent tool to create zip files with
an arbitrary file name and an arbitrary root (the top-level folder after
extracting a zip) from files and folders at arbitrary locations on the file
system.

Typical usage includes:

*   Deploy zip archives of Sphinx-documentation while releasing Python packages:

    .. code-block:: shell

        zip-folder --auto-root --outfile docs/_build/artifacts/mypackage-v1.0.0.zip docs/_build/html

    creates a file ``mypackage-v1.0.0.zip`` in ``docs/_build/artifacts`` that
    unzips as a folder ``mypackage-v1.0.0`` containing the files originally in
    ``docs/_build/html/``.

*   Create zip files pulled together from different locations, for emailing:

    .. code-block:: shell

        zip-folder -a -o report.zip ./report2020-01.tex /scratch/project/plots/*.pdf

    creates a file ``report.zip`` that unzips as a folder
    ``report`` containing the file ``report2020-01.tex`` and all the pdf files
    originally in ``/scratch/project/plots/``.

    .. code-block:: shell

        zip-folder -f report2020-01 -o report.zip ./report2020-01.tex /scratch/project/plots/*.pdf

    does the same, but unzips as a folder ``report2020-01`` instead of ``report``.



Development of zip-files happens on `Github`_.


Installation
------------

To install the latest released version of zip-files, run this command in your terminal:

.. code-block:: shell

    pip install zip_files

This is the preferred method to install zip-files, as it will always install
the most recent stable release.  It will result in the executable commands
``zip-files`` and ``zip-folder`` being added to your environment's ``bin``
folder.

.. _Github: https://github.com/goerz/zip_files


Usage
-----

zip-files
~~~~~~~~~

.. code-block:: console


    Usage: zip-files [OPTIONS] [FILES]...

      Create a zip file containing FILES.

    Options:
      -h, --help                      Show this message and exit.
      --version                       Show the version and exit.
      --debug                         Activate debug logging.
      -f, --root-folder ROOT_FOLDER   Folder name to prepend to FILES inside the
                                      zip file.
      -c, --compression [stored|deflated|bzip2|lzma]
                                      Zip compression method. The following
                                      methods are available: "stored": no
                                      compression; "deflated": the standard zip
                                      compression method; "bzip2": BZIP2
                                      compression method (part of the zip standard
                                      since 2001); "lzma": LZMA compression method
                                      (part of the zip standard since 2006).
                                      [default: deflated]
      -a, --auto-root                 If given in combination with --outfile, use
                                      the stem of the OUTFILE (without path and
                                      extension) as the value for ROOT_FOLDER
      -o, --outfile OUTFILE           The path of the zip file to be written. By
                                      default, the file is written to stdout.


zip-folder
~~~~~~~~~~

.. code-block:: console

    Usage: zip-folder [OPTIONS] FOLDER

      Create a zip file containing the FOLDER.

    Options:
      -h, --help                      Show this message and exit.
      --version                       Show the version and exit.
      --debug                         Activate debug logging.
      -f, --root-folder ROOT_FOLDER   Folder name to use as the top level folder
                                      inside the zip file (replacing FOLDER).
      -c, --compression [stored|deflated|bzip2|lzma]
                                      Zip compression method. The following
                                      methods are available: "stored": no
                                      compression; "deflated": the standard zip
                                      compression method; "bzip2": BZIP2
                                      compression method (part of the zip standard
                                      since 2001); "lzma": LZMA compression method
                                      (part of the zip standard since 2006).
                                      [default: deflated]
      -a, --auto-root                 If given in combination with --outfile, use
                                      the stem of the OUTFILE (without path and
                                      extension) as the value for ROOT_FOLDER
      -o, --outfile OUTFILE           The path of the zip file to be written. By
                                      default, the file is written to stdout.
