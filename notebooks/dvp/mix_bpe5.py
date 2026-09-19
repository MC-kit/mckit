import marimo

__generated_with = "0.23.13"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Compute composition of boron and polyethilen

    dvp 2024.10.31


    Create mix of wgt5% boron and polyethilen (remaining).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setup
    """)
    return


@app.cell
def _():
    import sys

    from pathlib import Path

    from mckit import Composition, Element, Material

    return Composition, Element, Path, sys


@app.cell
def _(sys):
    print(sys.version)
    print(sys.prefix)
    return


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %config Completer.use_jedi = False
    return


@app.cell
def _(Path):
    HERE = Path.cwd()
    ROOT = HERE.parent.parent
    dst =  ROOT / "wrk/bpe5.txt"
    return (dst,)


@app.cell
def _(dst):
    dst.parent.mkdir(exist_ok = True)
    return


@app.cell
def _():
    boron_fraction = 0.05
    polyethylene_fraction = 1.0 - boron_fraction
    mix_number = 170023 # free slot in up-mi-24-08-27.xlsx material index for mapstp
    return boron_fraction, mix_number, polyethylene_fraction


@app.cell
def _(Element):
    def mk_element(name: str):
        return Element(name, lib="31c")

    return (mk_element,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Computation
    """)
    return


@app.cell
def _(Composition, mk_element):
    boron = Composition(atomic=[(mk_element("B"), 1.0)]).expand()
    return (boron,)


@app.cell
def _(boron):
    boron.mcnp_repr()
    return


@app.cell
def _(Composition, mk_element):
    polyethylene = Composition(atomic = [(mk_element("C"), 1.0), (mk_element("H"), 2.0)]).expand()
    return (polyethylene,)


@app.cell
def _(polyethylene):
    polyethylene.mcnp_repr()
    return


@app.cell
def _(
    Composition,
    boron,
    boron_fraction,
    mix_number,
    polyethilen,
    polyethylene,
    polyethylene_fraction,
):
    bpe5 = Composition.mixture(
        (boron, boron_fraction / boron.molar_mass),
        (polyethylene, polyethylene_fraction / polyethilen.molar_mass),
    ).rename(mix_number)
    return (bpe5,)


@app.cell
def _(bpe5):
    bpe5.mcnp_repr()
    return


@app.cell
def _(bpe5, dst):
    dst.write_text(bpe5.mcnp_repr().replace("170023", "17023\n       "))
    return


if __name__ == "__main__":
    app.run()
