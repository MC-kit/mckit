.. image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
   :target: https://github.com/MC-kit/mckit/graphs/commit-activity

.. image:: https://github.com/MC-kit/mckit/workflows/Tests/badge.svg
   :target: https://github.com/MC-kit/mckit/actions

.. image:: https://codecov.io/gh/MC-kit/mckit/branch/devel/graph/badge.svg?token=05OFBQS3RX
   :target: https://codecov.io/gh/MC-kit/mckit

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
    :target: https://pycqa.github.io/isort/

.. image:: https://img.shields.io/github/license/MC-kit/mckit
   :target: https://github.com/MC-kit/mckit

.. image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :target: https://github.com/PyCQA/bandit
    :alt: Security Status


MCKIT: MCNP model and results processing utilities
==================================================

The mckit package provides a programming framework and command line tools to manipulate complex MCNP models.
When a model is rather complex and its description occupies thousands of text lines it becomes hard to modify it and integrate several model manually.
The package automates integration process.

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

    pip3 install mckit


Installing from github.com:

.. code-block:: bash

    pip3 install git+https://github.com/MC-kit/mckit.git


Versioning
----------

This software follows `Semantic Versioning`_

.. _Semantic Versioning: http://semver.org/


Contributors
------------

* `Roman Rodionov <mailto:r.rodionov@iterrf.ru>`_
* `Dmitri Portnov <mailto:dmitri_portnov@yahoo.com>`_
