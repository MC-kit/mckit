=================================
Welcome to mckit's documentation!
=================================

.. todo::

   The document is in progress.


.. todo::

   Add English version

Пакет mckit предназначен для облегчения работы с кодами радиационного транспорта
и упрощения процесса анализа полученных результатов. Основной средой для работы
предполагается использовать jupyter notebook.

Usage
=====

Command line interface
----------------------

.. click:: mckit.cli.runner:mckit
   :prog: mckit
   :nested: full


Основные задачи
===============

1. Упрощение процесса подготовки и интеграции моделей.

2. Упрощение описания геометрии моделей.

3. Обработка результатов расчетов нейтронного и гамма транспорта.

4. Автоматическая подготовка распределенного источника гамма-излучения для
   расчета SDDR (Shutdown dose rate).

5. Представление результатов.


Details
=======

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorial
   surface
   transformation
   material
   readme
   modules
   mcnp-model
   mcnp-parser
   developer
   license
   todo



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
