import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Rotation matrix demo

    Rotation matrix is defined by coordinates of new axes orts $[e_{x}', e_y', e_z']$, which present coordinates of the new orts in the original one: $[e_x, e_y, e_z]$.
    Rotation of a given vector $v=[v_x,v_y, v_z]$ in original coordinates, means linear combination of $v_x \cdot e_x' + v_y \cdot e_y' + v_z \cdot e_z' $.

    The new orts form columns of the rotation matix in C-format for usuage in numpy-like code.

    MCNP uses Fortran presentation in the transformation specs.

    So, for the MCNP specification the transformation matrix should be saved as transposed, and transposed back on reading.
    """)
    return


@app.cell
def _():
    import sys

    import numpy as np

    return np, sys


@app.cell
def _():
    from mckit import Transformation

    return (Transformation,)


@app.cell
def _(np):
    def calc_z_rotation(theta: float):
        """Compute matirix for rotation around z-axis.

        Parameters
        ----------
        theta
            rotation angle, radians

        Returns
        -------
            numpy presentation of the rotation matrix
        """
        return np.array(
            [
                [np.cos(theta), -np.sin(theta), 0],
                [np.sin(theta), np.cos(theta), 0],
                [0,             0,             1],
            ],
            dtype=np.float64
        )

    return (calc_z_rotation,)


@app.cell
def _(calc_z_rotation, np):
    r4 = calc_z_rotation(np.pi/4)
    r4
    return (r4,)


@app.cell
def _(r4):
    r4 @ [-1, -1, 0]
    return


@app.cell
def _(Transformation, r4):
    tr = Transformation(rotation=r4)
    return (tr,)


@app.cell
def _(tr):
    tr.apply2point([1, 0, 0])
    return


@app.cell
def _(Transformation, np, sys):
    def print_transformation(tr: Transformation, out = sys.stdout) -> None:
        t = np.array(tr.get_words()).reshape((4,6))
        for r in t:
            print("   ", *(x.rjust(6) for x in r if x != " "), file=out)

    return (print_transformation,)


@app.cell
def _(print_transformation, tr):
    print_transformation(tr)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Some adhoc computations
    """)
    return


@app.cell
def _(mo, theta):

    mo.md(f"Rotate XZ plane by {theta} degrees counter-clockwise")
    return


@app.cell
def _():
    theta = 22.5
    return (theta,)


@app.cell
def _(calc_z_rotation, np, theta):
    r_theta = calc_z_rotation(theta*np.pi/180)
    r_theta
    return


@app.cell
def _(Transformation, calc_z_rotation, np, print_transformation):
    print_transformation(Transformation(rotation=calc_z_rotation(11.25*np.pi/180.0)))
    return


@app.cell
def _(calc_z_rotation, np):
    def print_xy_basis(angle):
        t = calc_z_rotation(angle*np.pi/180)
        print(*("{:.7g}".format(t) for t in t.ravel()[:-3]))

    return (print_xy_basis,)


@app.cell
def _(print_xy_basis):
    print_xy_basis(22.5 + 11.25)
    return


if __name__ == "__main__":
    app.run()
