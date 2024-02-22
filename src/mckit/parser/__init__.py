from __future__ import annotations

from mckit.parser.common.utils import RE_C_COMMENT, drop_c_comments
from mckit.parser.mcnp_input_sly_parser import ParseResult, from_file, from_stream, from_text
from mckit.parser.meshtal_parser import read_meshtal

__all__ = [
    "ParseResult",
    "RE_C_COMMENT",
    "drop_c_comments",
    "from_file",
    "from_stream",
    "from_text",
    "read_meshtal",
]
