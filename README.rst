*MCKIT*: MCNP model and results processing utilities
====================================================



|Maintained| |License| |Versions| |PyPI| |Docs|

.. contents::


Description
-----------

The mckit package provides a programming framework and command line tools to manipulate complex MCNP models.
When a model is rather complex and its description occupies thousands of text lines it becomes hard to modify it and integrate several model manually.
The package automates integration process.

More details in documentation_.

.. TODO The complete documentation is available in the following languages:

.. * `English documentation`_
.. * `Russian documentation`_

.. .. _English documentation: https://mckit.readthedocs.io/en/latest/
.. .. _Russian documentation: https://mckit.readthedocs.io/ru/latest/

.. contents:: Table of contents

Usage
-----

Command line interface
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    Usage: mckit [OPTIONS] COMMAND [ARGS]...

      Tools to process MCNP models and results

    Options:
      --override / --no-override
      --version                   Show the version and exit.
      -v, --verbose               Log debugging info to stderr.  [default: False]
      -q, --quiet                 Suppress info to stderr.  [default: False]
      --logfile / --no-logfile    Log to file.  [default: True]
      --profile_mem               Profile peak memory use.  [default: False]
      --help                      Show this message and exit.

    Commands:
      check      Read MCNP model(s) and show statistics and clashes.
      compose    Merge universes and envelopes into MCNP model using merge...
      concat     Concat text files.
      decompose  Separate an MCNP model to envelopes and filling universes
      split      Splits MCNP model to text portions (opposite to concat)
      transform  Transform MCNP model(s) with one of specified transformation.


Library
~~~~~~~

The library allows subtraction and merging models, renaming objects (cells, surfaces, compositions, universes),
simplification of cell expressions (removing redundant surfaces), homogenization, computation of cell volumes and
material masses, and more.

.. code-block:: python

    LOG.info("Loading c-model envelopes")
    envelopes = load_model(str(CMODEL_ROOT / "c-model.universes/envelopes.i"))

    cells_to_fill = [11, 14, 75]
    cells_to_fill_indexes = [c - 1 for c in cells_to_fill]

    LOG.info("Attaching bounding boxes to c-model envelopes %s", cells_to_fill)
    attach_bounding_boxes(
        [envelopes[i] for i in cells_to_fill_indexes], tolerance=5.0, chunk_size=1
    )
    LOG.info("Backing up original envelopes")
    envelopes_original = envelopes.copy()

    antenna_envelop.rename(start_cell=200000, start_surf=200000)

    LOG.info("Subtracting antenna envelop from c-model envelopes %s", cells_to_fill)
    envelopes = subtract_model_from_model(
        envelopes, antenna_envelop, cells_filter=lambda c: c in cells_to_fill
    )
    LOG.info("Adding antenna envelop to c-model envelopes")
    envelopes.add_cells(antenna_envelop, name_rule="clash")
    envelopes_path = "envelopes+antenna-envelop.i"
    envelopes.save(envelopes_path)
    LOG.info("The model of HFSR in envelopes is saved to %s", envelopes_path)



Installation
------------

Installing from pypi:

.. code-block:: bash

    pip install mckit
    # or
    uv pip install mckit 


Installing from github.com:

.. code-block:: bash

    pip install git+https://github.com/MC-kit/mckit.git
    # or
    uv pip install git+https://github.com/MC-kit/mckit.git

Some specific: in development environment we use uv_, just_, ruff_.

To setup development environment, run:

.. code-block:: shell

  just install | reinstall

To build documentation, run:

.. code-block:: shell

   just docs        # - for local online docs rendering, while editing 
   just docs-build  # - to build documentation 

To release, run:

.. code-block:: shell

  just bump [major|minor|patch]  # - in `devel` branch
  
Then merge devel to master (via Pull Request) and if all the checks are passed create Release. Manually.


Versioning
----------

This software follows `Semantic Versioning`_

.. _Semantic Versioning: http://semver.org/


Contributors
------------

* `Roman Rodionov (@rrn)
* `Dmitri Portnov <mailto:dmitri_portnov@yahoo.com>`_


.. Links

.. _documentation: https://mckit.readthedocs.io/en/latest
.. _uv: https://github.com/astral-sh/uv
.. _just: https://github.com/casey/just
.. _ruff: https://github.com/astral-sh/ruff


.. Substitutions

.. |Maintained| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
   :target: https://github.com/MC-kit/mckit/graphs/commit-activity
.. |Tests| image:: https://github.com/MC-kit/mckit/workflows/Tests/badge.svg
   :target: https://github.com/MC-kit/mckit/actions?workflow=Tests
   :alt: Tests
.. |License| image:: https://img.shields.io/github/license/MC-kit/mckit
   :target: https://github.com/MC-kit/mckit
.. |Versions| image:: https://img.shields.io/pypi/pyversions/mckit
   :alt: PyPI - Python Version
.. |PyPI| image:: https://img.shields.io/pypi/v/mckit
   :target: https://pypi.org/project/mckit/
   :alt: PyPI
.. |Docs| image:: https://readthedocs.org/projects/mckit/badge/?version=latest
   :target: https://mckit.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
