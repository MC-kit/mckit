import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", auto_download=["html"])

with app.setup:
    import logging
    import sys

    from pathlib import Path
    from textwrap import dedent

    import lark_cython
    import numpy as np
    import rich

    from rich.console import Console
    from rich.logging import RichHandler
    from rich.traceback import install



    from lark import Lark, Transformer, Token, v_args

    MY_NAME = "try-lark-parser"

    # Use Rich as the default traceback handler for all uncaught exceptions
    install(show_locals=True)

    def get_logger(suffix: str | None = None) -> logging.Logger:
        """Get the package specific logger.

        Parameters
        ----------
            suffix
                The requested logger name, optional

        Returns
        -------
            The logger for name prepended with the package name, if provided,
            otherwise the root MY_NAME logger
        """
        return logging.getLogger(MY_NAME if suffix is None else MY_NAME + "." + suffix)

    # File handler
    file_handler = logging.FileHandler("try-lark-parser-debug.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=Console(), 
                markup = True,
                rich_tracebacks=True,
                show_level = False,
                show_path = False, 
                show_time = False,
            ),
            file_handler,
        ],
    )

    logger = logging.getLogger("lark")
    for _hdlr in logger.handlers:
        logger.removeHandler(_hdlr)
    logger.disabled = False
    logger.setLevel(logging.DEBUG)

    logger = get_logger()
    logger.disabled = False
    logger.setLevel(logging.DEBUG)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    def _():
        nb_common_path = Path(mo.notebook_dir().parent, "nb_common").absolute()
        assert nb_common_path.is_dir(), nb_common_path
        nb_common_name = str(nb_common_path)
        if not nb_common_name in sys.path:
            sys.path.append(str(nb_common_path))

    _()

    from config_utils import HOST, check_file, find_git_root
    HOST
    return (find_git_root,)


@app.cell
def _(find_git_root):
    ROOT = find_git_root()
    ROOT
    return


@app.cell
def _():
    text="""
       1 2
       3 4
    """
    return (text,)


@app.cell
def _():
    grammar=r"""
    start: _N* matrix _N*

    _N: /\r?\n/

    matrix: (vector _N)+

    # This works but the tree is too complicated with long left branch
    # matrix: [matrix _N] vector

    vector: float+

    ?float: SIGNED_NUMBER

    // Numbers
    %import common.SIGNED_NUMBER
    // Separators / whitespace (ignored)
    %import common.WS_INLINE
    %ignore WS_INLINE
    """
    return (grammar,)


@app.cell
def _(grammar):
    parser = Lark(grammar, parser="lalr", cache=False, debug=True)
    return (parser,)


@app.cell
def _(parser, text):
    list(map(lambda t: f"{t.type}: {t.value}", parser.lex(text)))
    return


@app.cell
def _(parser, text):
    def _():
        tree = parser.parse(text)
        return tree
    rich.print(_())
    return


@app.cell
def _(parser, text):
    parsed_tokens = []
    try:
        tree = parse_with_progress(parser, text, parsed_tokens=parsed_tokens)
        with Path("try-lark-parser-tree.txt").open("w") as _f:
            rich.print(tree, file=_f)
    finally:
        with Path("try-lark-parser-tokens.txt").open("w") as _f:
            for t in parsed_tokens:
                rich.print(t, file=_f)
    return parsed_tokens, tree


@app.cell
def _(parsed_tokens):
    rich.print(parsed_tokens)
    return


@app.cell
def _(MeshtalTransformer, tree):
    transformer = MeshtalTransformer()
    result = transformer.transform(tree)
    rich.print(result)
    return


@app.function
def parse_with_progress(parser: Lark, text: str, start=None, parsed_tokens: list[str] | None = None):
    if parsed_tokens is not None:
        del parsed_tokens[:]
    pi = parser.parse_interactive(text, start=start)
    for i, token in enumerate(pi.iter_parse()):
        if parsed_tokens is not None:
            parsed_tokens.append(dedent(
                f"""\
                {i}:
                    tp: {token.type}
                    vl: {token.value if token.type not in ("_NL", "_SP") else "..."} 
                    ln: {token.line}
                    ps: {token.start_pos}
                    {pi.pretty().replace("Parser choices", "ch")}
                """))
    return pi.resume_parse()


if __name__ == "__main__":
    app.run()
