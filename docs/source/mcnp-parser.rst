.. _mcnp:

Парсер входного файла MCNP
==========================

Входной файл MCNP состоит из опционального блока сообщений (Message Block) и
и трех блоков: блок ячеек, блок поверхностей и блок данных. Блок ячеек
начинается с карты заглавия (title card), которая вкратце описывает задачу.
Все блоки разделяются между собой одной пустой строкой (Blank Line Delimiter).
Последний блок рекомендуется заканчивать пустой строкой. Все что идет после нее
-- игнорируется. Структура входного файла MCNP:

.. line-block::
    Message Block  // опционально
    Blank Line Delimiter  // В случае, если есть Message Block
    Title Card
    Cell Card 1
    Cell Card 2
    .
    .
    Blank Line Delimiter
    Surface Card 1
    Surface Card 2
    .
    .
    Blank Line Delimiter
    Data Card 1
    Data Card 2
    .
    .
    Blank Line Delimiter // рекомендуется
    Anything else        // опционально

Message Block
-------------

Служит для передаче параметров коду (например параметров командной строки).
Начинается со строки "MESSAGE:". Символы $ и & являются маркерами конца строки.
Все карты до пустой строки являются продолжением.

Формат карт
-----------

Все карты должны помещаться в 80 колонок (за исключением комментариев). Все
карты вводятся в горизонтальном формате, хотя карты данных (Data cards) могут
вводиться и в вертикальном формате. Знак $ - служит началом комментария в карте.
Все символы после него и до конца строки считаются комментарием. Выделим еще
отдельный тип комментариев (comment cards) -- мы отнесем их к информационным,
не относящимся ни к одной реальной карте (в отличие от $). Они начинаются с
символа "C", находящегося в колонке 1-5, за которым следует хотя бы один пробел.

Горизонтальный формат
^^^^^^^^^^^^^^^^^^^^^

Карты ячеек, поверхностей и данных должны начинаться в первых пяти колонках.
Сначала идут название карты или номер и спецификатор типа частицы, затем
остальные данные, разделяемые пробелами. Пробелы в первых пяти колонках
означают, что далее идет продолжение ранее введенной карты. Символ & означает,
что на следующей строке будет продолжение карты (символы могут быть в колонках
1 - 80). Специальные символы:

#. nR - означает повторить предыдущий токен n раз.

#. nI - означает сделать линейную интерполяцию между предыдущим и следующим
   значениями (вставить n значений). Например: 1 4I 6 эквивалентно 1 2 3 4 5 6.

#. nILOG - вставить логарифмическую интерполяцию. 0.01 2ILOG 10 эквивалентно
   0.01 0.1 1 10.

#. xM - означает умножение. Предыдущее значение (вхождение) умножается на x.
   1 1 2M 2M 2M 2M 4M 2M 2M эквивалентно 1 1 2 4 8 16 64 128 256

#. nJ - оставить следующие n значений по умолчанию (перепрыгнуть n занчений).

Вертикальный формат
^^^^^^^^^^^^^^^^^^^

Вертикальный формат полезен для параметров ячеек и распределений источника.
Символ & не нужен и игнорируется. R, M, I, J интерпретируются вертикально, а
не горизонтально.

.. math::

   \begin{array}{cc} \# & S_1 & S_2 & \cdots & S_m\\
                K_1& D_{11} & D_{12} & \cdots & D_{1m}\\
                K_2& D_{21} & D_{22} & \cdots & D_{2m}\\
                \vdots&\vdots&\vdots&\ddots&\vdots\\
                K_n& D_{n1} & D_{n2} & \cdots & D_{nm}
    \end{array}

#. Символ # должен быть в одной из колонок 1 - 5.

#. Каждая строка должна быть не более 80 символов.

#. Каждая колонка от :math:`S_i` до :math:`D_{li}`, где :math:'l' может быть
   меньше, чем n, представляет собой отдельную входную карту.

#. :math:`S_i` должно быть правильным именем MCNP карты. Это все параметры
   ячеек, все параметры поверхностей, и все прочие параметры.

#. Значения :math:`D_{1i}` - :math:`D_{ni}` должны быть допустимыми значениями
   для параметра с именем :math:`S_i`.

#. Если :math:`D_{ji}` - не пустое, то :math:`D_{j,i-1}` тоже должно быть не
   пустым. Можно использовать J.

#. :math:`S_i` не должно появляться где-либо еще во входном файле.

#. :math:`K_j` - опциональные целые числа. Но если хотябы одно задано, то и все
   остальные должны быть заданы. Если они заданы, то не должны использоваться
   символы повторений, такие как 9R, 9M.

#. Если :math:`S_i` - параметр ячейки, то :math:`K_j` должны быть именами ячеек.
   Тоже самое справедливо и для поверхностей.

Спецификаторы частиц
--------------------

Спецификаторы типа частиц необходимы для некоторых карт: IMP, EXT, FCL, WWN,
WWE, WWP, WWGE, DXT, DXC, F, F5X, F5Y, F5Z, FMESH, PHYS, ELPT, ESPLT, TSPLT,
CUT, PERT. Спецификаторы частиц прибавляются через символ ":", за которым
следует собственно сам спецификатор (N, P, E). Если допустимо, то несколько
спецификаторов могут быть перечисленны через запятую.

Cell Cards
----------

- Cell card = j m d geom params | j LIKE n BUT list

- j = cell number; 1 <= j <= 99999 (version specific). If TRCL card present,
  j <= 999.

- m = 0 if cell void | material number if cell contains material.

- d = absent if cell is a void | cell material density. Positive - atomic
  density in units of :math:`10^{24}` atoms/cm\ :sup:`3`. If negative - in units
  of g/cm\ :sup:`3`.

- geom = specification of geometry of cell. Signed surface numbers with
  boolean operations (:, , #).

- params = optional specification of cell parameters by entries of keywoed=value
  form. Blank is equivalent to the equal sign. Allowed keywords: IMP, VOL, PWT,
  EXT, FCL, WWN, DXC, NONU, PD, TMP, U, TRCL, LAT, FILL.

- n = number of another cell.

- list = same as params except this is values which makes cell n and j
  different.

Surface cards
-------------

- Surface card = j n a list

- j = surface number: 1<=j<=99999. Preceded by asterisk for reflecting surface
  and with plus for a white boundary. j <=999 for surfaces of cells with TRCL
  parameter.

- n = absent for no coordinate transformation. >0 - the number of TRn card;
  <0 surface j is periodic with surface n.

- a = equation mnemonic (P, PX, SO, etc.)

- list = one to ten entries - surface coefficients.

Surface defined by macrobodies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not yet.

Data cards
----------

Problem type card
^^^^^^^^^^^^^^^^^

MODE x\ :sub:`1` ... x\ :sub:`n`
x\ :sub:`i` = N for neutron, P for photon, E for electron transport

Cell volume card
^^^^^^^^^^^^^^^^

VOL x\ :sub:`1` ... x\ :sub:`n`
VOL NO x\ :sub:`1` ... x\ :sub:`n`
x\ :sub:`i` = volume of cell i.
NO = no volumes or areal are calculated.

Surface area card
^^^^^^^^^^^^^^^^^

AREA x\ :sub:`1` ... x\ :sub:`n`
x\ :sub:`i` = area of surface i.

Universe card
^^^^^^^^^^^^^

U=n if n negative - checks are turned off.

Transformation card
^^^^^^^^^^^^^^^^^^^

- transformation card = [*]TRn translation [rotation] [M]

- n = number

- translation = O1 O2 O3 - displacement vector

- rotation = B1 ... B9 - rotation matrix. If * - these are degrees.
  All nine; 6 values; 5 values; 3 values; none.

- M = 1 (default) translation is the location of the origin of the auxiliary
  coordinate system defined in the main system | -1 location of the main system
  origin defined in the auxiliary system.

Material card
^^^^^^^^^^^^^

- material card = Mn zaid_frac_pairs params

- n = material number

- zaid_frac_pairs = ZAID fraction [ZAID fraction]

- ZAID = ZZZAAA[.nnX]; nn - library identifier; X - class of data.

- fraction = atomic fraction if positive and weight fraction if negative.

- params = keyword=value [keyword=value]; = - optional

- keyword = GAS | ESTEP | NLIB | PLIB | PNLIB | ELIB | COND

Формальная граматика
--------------------

Cell card
^^^^^^^^^

.. code::

    cell-card = name material geometry params | name LIKE n BUT params
    name, n = int (>0)
    material = 0 | mat_name density
    mat_name = int (>0)
    density = float
    geometry = expression
    expression = term : expression | term
    term = operand term | factor
    factor = surf_name | #(expression) | #name | (expression)
    surf_name = int
    params = kwpair | kwpair params
    kwpair = int_pair | float_pair | complex_pair
    int_pair = kwint int | kwint = int
    kwint = U | TRCL
    float_pair = kwfloat float | kwfloat = float
    kwfloat = IMP:N | IMP:P | IMP:E | VOL
