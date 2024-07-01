from __future__ import annotations

from typing import TYPE_CHECKING

import sly

import mckit.parser.common.utils as pu

from mckit.body import Body, Shape
from mckit.material import Material
from mckit.parser.common import CellStrictIndex, CompositionStrictIndex
from mckit.parser.common import Lexer as LexerBase
from mckit.parser.common import SurfaceStrictIndex, TransformationStrictIndex
from mckit.surface import Surface
from mckit.transformation import Transformation
from mckit.utils import filter_dict
from mckit.utils.indexes import Index

CELL_WORDS = {"U", "MAT", "LAT", "TMP", "RHO", "VOL", "PMT"}


def intern_cell_word(word: str):
    word = pu.ensure_upper(word)
    word, res = pu.internalize(word, CELL_WORDS)
    if not res:
        raise pu.ParseError(f"'{word}' is not a valid word for cell specification")
    return word


if TYPE_CHECKING:
    from typing import ClassVar


# noinspection PyPep8Naming,PyUnboundLocalVariable,PyUnresolvedReferences,SpellCheckingInspection
class Lexer(LexerBase):
    literals: ClassVar = {":", "(", ")", "*", "#"}
    ignore = "[ \t,=]"
    tokens: ClassVar = {
        INT_ATTR,
        IMP,
        FLOAT_ATTR,
        TRCL,
        FILL,
        INTEGER,
        FLOAT,
        ZERO,
        LIKE,
        BUT,
        N,
        P,
        E,
    }
    INT_ATTR = "U|MAT|LAT|PMT"
    IMP = "IMP"
    FLOAT_ATTR = "TMP|RHO|VOL"
    TRCL = "TRCL"
    FILL = "FILL"
    LIKE = "LIKE"
    BUT = "BUT"
    N = "N"
    P = "P"
    E = "E"

    @_(pu.FLOAT)
    def FLOAT(self, token):
        return self.on_float(token)


# noinspection PyUnresolvedReferences
class Parser(sly.Parser):
    tokens = Lexer.tokens

    def __init__(
        self,
        cells,
        surfaces,
        transformations,
        compositions,
        comments=None,
        trailing_comments=None,
        original=None,
    ):
        sly.Parser.__init__(self)
        self._cells = cells
        self._surfaces = surfaces
        self._transformations = transformations
        self._compositions = compositions
        self._comments = comments
        self._trailing_comments = trailing_comments
        self._original = original

    @property
    def cells(self):
        return self._cells

    @property
    def surfaces(self):
        return self._surfaces

    @property
    def transformations(self):
        return self._transformations

    @property
    def compositions(self):
        return self._compositions

    @property
    def comments(self):
        return self._comments

    @property
    def trailing_comments(self):
        return self._trailing_comments

    @property
    def original(self):
        return self._original

    def build_cell(self, geometry, options):
        if self.trailing_comments:
            options["comment"] = self.trailing_comments
        if self._original:
            options["original"] = self.original
        return Body(geometry, **options)

    @_("INTEGER cell_material cell_spec")
    def cell(self, p):
        geometry, options = p.cell_spec  # type: TGeometry, Optional[Dict[str, Any]]
        assert options is None or isinstance(options, dict)
        if options is None:
            options = {"name": p.INTEGER}
        else:
            options["name"] = p.INTEGER
        if p.cell_material is not None:
            composition_no, density = p.cell_material  # type: int, float
            composition = self.compositions[composition_no]
            if density > 0:
                material = Material(composition=composition, concentration=density * 1e24)
            else:
                material = Material(composition=composition, density=-density)
            options["MAT"] = material
        return self.build_cell(geometry, options)

    @_("INTEGER LIKE INTEGER BUT attributes")
    def cell(self, p):
        reference_body = self.cells[p[2]]
        options = filter_dict(reference_body.options, "original", "comment", "comment_above")
        options.update(p.attributes)
        options["name"] = p[0]
        new_body = Body(reference_body, **options)
        return self.build_cell(new_body, options)

    @_("INTEGER float")
    def cell_material(self, p):
        return p.INTEGER, p.float

    @_("ZERO")
    def cell_material(self, _):
        return None

    @_("expression attributes")
    def cell_spec(self, p):
        return p.expression, p.attributes

    @_("expression")
    def cell_spec(self, p):
        return p.expression, None

    @_('expression ":" term')
    def expression(self, p):
        result = p.expression + p.term
        result.append("U")
        return result

    @_("term")
    def expression(self, p):
        return p.term

    @_("term factor")
    def term(self, p):
        res = p.term + p.factor
        res.append("I")
        return res

    @_("factor")
    def term(self, p):
        return p.factor

    @_('"#" "(" expression ")"')
    def factor(self, p):
        return [*p.expression, "C"]

    @_('"(" expression ")"')
    def factor(self, p):
        return p.expression

    @_('"-" integer')
    def factor(self, p):
        surface = self.surfaces[p.integer]
        return [Shape("C", surface)]

    @_('"+" integer')
    def factor(self, p):
        surface = self.surfaces[p.integer]
        return [Shape("S", surface)]

    @_('"#" integer')
    def factor(self, p):
        body = self.cells[p.integer]
        return [Shape("C", body)]

    @_("integer")
    def factor(self, p):
        item: int = p.integer
        if 0 < item:
            opc = "S"
        else:
            opc = "C"
            item = -item
        surface: Surface = self.surfaces[item]
        return [Shape(opc, surface)]

    @_("attributes attribute")
    def attributes(self, p):
        result = p.attributes
        result.update(p.attribute)
        return result

    @_("attribute")
    def attributes(self, p):
        return p[0]

    @_(
        "fill_attribute",
        "trcl_attribute",
        "imp_attribute",
        "float_attribute",
        "int_attribute",
    )
    def attribute(self, p):
        return p[0]

    @_('"*" FILL integer "(" transform_params ")"')
    def fill_attribute(self, p):
        translation, rotation, inverted = p.transform_params
        transformation = Parser.build_transformation(translation, rotation, True, inverted)
        fill = {"universe": p.integer, "transform": transformation}
        return {"FILL": fill}

    @_('FILL integer "(" transform_params ")"')
    def fill_attribute(self, p):
        translation, rotation, inverted = p.transform_params
        transformation = Parser.build_transformation(translation, rotation, False, inverted)
        fill = {"universe": p.integer, "transform": transformation}
        return {"FILL": fill}

    @_('FILL integer "(" integer ")"')
    def fill_attribute(self, p):
        transform_id: int = p[3]
        transformation = self.transformations[transform_id]
        fill = {"universe": p[1], "transform": transformation}
        return {"FILL": fill}

    @_("FILL integer")
    def fill_attribute(self, p):
        fill = {"universe": p.integer}
        return {"FILL": fill}

    @staticmethod
    def build_transformation(translation, rotation, in_degrees, inverted):
        return Transformation(
            translation=translation,
            rotation=rotation,
            indegrees=in_degrees,
            inverted=inverted,
        )

    @_('"*" TRCL "(" transform_params ")"')
    def trcl_attribute(self, p):
        translation, rotation, inverted = p.transform_params
        return {"TRCL": Parser.build_transformation(translation, rotation, True, inverted)}

    @_('TRCL "(" transform_params ")"')
    def trcl_attribute(self, p):
        translation, rotation, inverted = p.transform_params
        return {"TRCL": Parser.build_transformation(translation, rotation, False, inverted)}

    @_("TRCL integer")
    def trcl_attribute(self, p):
        transform_id: int = p.integer
        transformation = self.transformations[transform_id]
        return {"TRCL": transformation}

    @_("translation rotation")
    def transform_params(self, p):
        rotation, inverted = p.rotation
        return p.translation, rotation, inverted

    @_("translation")
    def transform_params(self, p):
        return p.translation, None, False

    @_("float float float")
    def translation(self, p):
        return list(p)

    @_("float float float float float float float float float INTEGER")
    def rotation(self, p):
        m = p[9]
        assert m in {-1, 1}, f"Invalid value for transformation M parameter {m}"
        return list(p)[:-1], m == -1

    @_(
        "float float float float float float float float float",
        "float float float float float float",
        "float float float float float",
        "float float float",
    )
    def rotation(self, p):
        return list(p), False

    #
    #  See MCNP, vol.I, p.3-7
    #  Example: IMP:E,P,N 1 1 0.
    #
    @_('IMP ":" particle_list float_list')
    def imp_attribute(self, p):
        number_of_particles = len(p.particle_list)
        if number_of_particles != len(p.float_list):
            while len(p.float_list) < number_of_particles:
                p.float_list.append(p.float_list[-1])
        return {"IMP" + k.upper(): v for k, v in zip(p.particle_list, p.float_list)}

    @_("float_list float")
    def float_list(self, p):
        return [*p.float_list, p.float]

    @_("float")
    def float_list(self, p):
        return [p.float]

    @_("particle_list particle")
    def particle_list(self, p):
        p.particle_list.append(p.particle)
        return p.particle_list

    @_("particle")
    def particle_list(self, p):
        return [p.particle]

    @_("N", "P", "E")
    def particle(self, p):
        return pu.ensure_upper(p[0])

    @_("FLOAT_ATTR float")
    def float_attribute(self, p):
        return {intern_cell_word(p.FLOAT_ATTR): p.float}

    @_("INT_ATTR integer")
    def int_attribute(self, p):
        return {intern_cell_word(p.INT_ATTR): p.integer}

    @_("FLOAT")
    def float(self, p):
        return p.FLOAT

    @_("integer")
    def float(self, p):
        return float(p[0])

    @_("INTEGER", "ZERO")
    def integer(self, p):
        return p[0]


def parse(
    text: str,
    cells: Index | None = None,
    surfaces: Index | None = None,
    transformations: Index | None = None,
    compositions: Index | None = None,
) -> Body:
    cells, surfaces, transformations, compositions = (
        x[1]() if x[0] is None else x[0]
        for x in zip(
            [cells, surfaces, transformations, compositions],
            [
                CellStrictIndex,
                SurfaceStrictIndex,
                TransformationStrictIndex,
                CompositionStrictIndex,
            ],
        )
    )
    original = text
    text = pu.drop_c_comments(text)
    text, comments, trailing_comments = pu.extract_comments(text)
    lexer = Lexer()
    parser = Parser(
        cells,
        surfaces,
        transformations,
        compositions,
        comments,
        trailing_comments,
        original,
    )
    return parser.parse(lexer.tokenize(text))
