"""Extract lost particles from MCNP output.

Create tables:
    - cell_fail, surface, cell_in, x, y, z, u, v, w, out_file, lp_no, hist_no
    - cell_fail, count  -  sorted by count in descending order

Create comin from MCNP plot by template replacing coordinates with coordinates of the most frequent
cell fail.

Adapted to old python versions available on HPCs.
"""

from __future__ import annotations

import re
import sqlite3 as sq
import sys

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

__appname__ = "extract_lost_particles"
__version__ = "0.1.3"

DESCRIPTION_START_RE = re.compile(r"^1\s+lost particle no.\s*(?P<lp_no>(\d+|\*\*\*))")
HISTORY_NO_RE = re.compile(r"history no.\s+(?P<hist_no>\d+)$")


# noinspection SqlDialectInspection,SqlNoDataSourceInspection
def setup_db(con: sq.Cursor) -> None:
    """Setup data base."""
    con.executescript(
        """
        drop table if exists lost_particles;
        create table lost_particles (
            cell_fail integer,
            surface integer,
            cell_in integer not null,
            x real not null,
            y real not null,
            z real not null,
            u real not null,
            v real not null,
            w real not null,
            lp_no integer not null,
            hist_no integer not null,
            out_file text not null
        );
        """
    )


def extract_descriptions(p: Path) -> Iterator[tuple[int, list[str]]]:
    """Extract lost particles descriptions from MCNP output file.

    Args:
        p: path to MCNP output file

    Yields:
        start line of portion, portion of lines corresponding to a lost particle
    """
    wait_description = True
    start_line = 0
    description = []
    with p.open() as fid:
        for i, line in enumerate(fid):
            if wait_description:
                if line.startswith("1   lost particle no."):
                    start_line = i + 1
                    description.append(line)
                    wait_description = False
            else:
                description.append(line)
                if len(description) > 15:
                    wait_description = True
                    yield start_line, description
                    description = []


@dataclass
class _Description:
    cell_fail: int | None
    surface: int | None
    cell_in: int
    x: float
    y: float
    z: float
    u: float
    v: float
    w: float
    lp_no: int
    hist_no: int


class ParseError(ValueError):
    pass


def _parse_description(lines: list[str]) -> _Description:
    """Extract information on lost particle from the text lines."""
    match = DESCRIPTION_START_RE.search(lines[0])
    if match is None:
        raise ParseError("Cannot find lost particle number")
    lp_no_str = match["lp_no"]
    if lp_no_str == "***":
        lp_no = 9999
    else:
        lp_no = int(lp_no_str)
    match = HISTORY_NO_RE.search(lines[0])
    if match is None:
        raise ParseError("Cannot find lost history number")
    hist_no = int(match["hist_no"])

    if "no cell found" in lines[0]:
        surface = int(lines[2].split()[-3])
        cell_fail = int(lines[3].rsplit(maxsplit=2)[-1])
        # line[6] may contain one of the following
        # point (x,y,z) is in cell     1439
        # the neutron  is in cell     1344.
        line6 = lines[6].strip()
        cell_in = int(line6.rsplit(maxsplit=2)[-1].rstrip("."))
        x, y, z = map(float, lines[8].split()[-3:])
        u, v, w = map(float, lines[9].split()[-3:])
    elif "no intersection found" in lines[0]:
        surface = None
        cell_fail = None
        line2 = lines[2].strip()
        cell_in = int(line2.split(".")[0].rsplit(maxsplit=2)[-1])
        x, y, z = map(float, lines[5].split()[-3:])
        u, v, w = map(float, lines[6].split()[-3:])
    else:
        msg = f"Unknown lost particles spec first line: {lines[0]}"
        raise ParseError(msg)

    return _Description(cell_fail, surface, cell_in, x, y, z, u, v, w, lp_no, hist_no)


def _process_file(p: Path, cur: sq.Cursor) -> None:
    with open("lp-details.txt", "a") as fid:
        out_file_name = str(p)
        for start_line, lines in extract_descriptions(p):
            print("-" * 20, file=fid)
            for line in lines:
                print(line, file=fid, end="")
            try:
                description = _parse_description(lines)
                cur.execute(
                    """
                    insert into lost_particles (
                        cell_fail,
                        surface,
                        cell_in,
                        x,
                        y,

                        z,
                        u,
                        v,
                        w,
                        lp_no,

                        hist_no,
                        out_file
                    )
                    values (?,?,?,?,?, ?,?,?,?,?, ?,?)
                """,
                    (
                        description.cell_fail,
                        description.surface,
                        description.cell_in,
                        description.x,
                        description.y,
                        description.z,
                        description.u,
                        description.v,
                        description.w,
                        description.lp_no,
                        description.hist_no,
                        out_file_name,
                    ),
                )
            except ParseError as ex:
                msg = f"Error parsing {p}: {start_line}"
                raise ParseError(msg) from ex


def main() -> None:
    """Workflow implementation."""
    db = "lost-particles.sqlite"
    if _collect_lost_particles(db):
        _analyze(db)
    else:
        print("Files not found")


def _analyze(db) -> None:
    with sq.connect(db) as con:
        cur = con.cursor()
        cell_fail_counts = cur.execute(
            """
            select
                cell_fail,
                count(*) cnt
            from lost_particles
            group by cell_fail
            order by cnt desc
            """
        ).fetchall()
        with open("lp-cell-fails-count.csv", "w") as fid:
            for t in cell_fail_counts:
                print(*t, sep=",", file=fid)
        lost_coordinates = cur.execute(
            """
            select
                cell_fail,
                surface,
                cell_in,
                x, y, z,
                u, v, w
            from lost_particles
            order by
                cell_fail,
                surface,
                cell_in,
                x, y, z,
                u, v, w
            """
        ).fetchall()
        with open("lp-coordinates.csv", "w") as fid:
            for t in lost_coordinates:
                print(*t, sep=",", file=fid)

        coordinates_to_work = cur.execute(
            """
                select
                    x, y, z
                from lost_particles
                where
                    cell_fail = ?
                limit 1
            """,
            (cell_fail_counts[0][0],),
        ).fetchone()
        coordinates_text = " ".join(map(str, coordinates_to_work))
        origin_text = "origin " + coordinates_text + " &"
        comin_path = Path("comin")
        if comin_path.exists():
            comin_text = Path("comin").read_text()
            comin_lines = comin_text.split("\n")
            comin_lines[0] = origin_text
            new_comin_text = "\n".join(comin_lines)
        else:
            new_comin_text = origin_text[:-1]
        with open("comin", "w") as fid:
            print(new_comin_text, file=fid)


def _collect_lost_particles(db: str) -> bool:
    files = _collect_files()
    if not files:
        return False
    with sq.connect(db) as con:
        cur = con.cursor()
        setup_db(cur)
        for f in files:
            _process_file(f, cur)
    return True


def _collect_files() -> list[Path]:
    args = sys.argv[1:]
    if args:
        files = [Path(a) for a in args]
    else:
        files = [a for a in Path.cwd().glob("*.o")]
    return files


if __name__ == "__main__":
    main()
