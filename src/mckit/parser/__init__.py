from __future__ import annotations

import warnings

from mckit.parser.common.utils import RE_C_COMMENT, drop_c_comments
from mckit.parser.mcnp_input_sly_parser import ParseResult, from_file, from_stream, from_text

warnings.warn(
    "mckit.parser.meshtal_parser is deprecated and will be removed in version 0.11. "
    "Use mckit.parser.meshtal_lark_parser instead.",
    DeprecationWarning,
    stacklevel=2,
)
from mckit.parser.meshtal_parser import read_meshtal

__all__ = [
    "RE_C_COMMENT",
    "ParseResult",
    "drop_c_comments",
    "from_file",
    "from_stream",
    "from_text",
    "read_meshtal",
]
