"""Extract lost particles from MCNP output.

Collects information on lost particles in SQLite database.
Subsequent runs are collected incrementally.

if no lost particles found, just logs this

Otherwise, analyzes the database and creates CSV tables:
    - "lp-coordinates.csv":
        cell_fail, surface, cell_in, x, y, z, u, v, w, out_file, lp_no, hist_no
    - "lp-cell-fails-count.csv":
       cell_fail, count  -  sorted by count in descending order

Besides, creates comin file for MCNP plot.
May use template comin replacing coordinates with coordinates of the most leaking
cell. If the template is not provided creates default comin file.

Adapted to old python versions available on HPCs.
"""

from __future__ import annotations

import logging
import re
import sqlite3 as sq
import sys

from dataclasses import dataclass, field
from pathlib import Path

__appname__ = "extract_lost_particles"
__version__ = "0.3.1"

from sqlite3 import Cursor

DESCRIPTION_START_RE = re.compile(r"^1\s+lost particle no.\s*(?P<lp_no>(\d+|\*\*\*))")
HISTORY_NO_RE = re.compile(r"history no.\s+(?P<hist_no>\d+)$")
NPS_COLL_CTME_RE = re.compile(r"^ dump no\..*nps =\s+(?P<nps>\d+)\s+coll =\s+(?P<coll>\d+)\s+ctm =\s+(?P<ctme>\d+(\.\d+)?)")

LOG = logging.getLogger(__name__)

def setup_db(con: sq.Cursor) -> None:
    """Setup database."""
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
        drop table if exists nps_coll_ctme;
        create table nps_coll_ctme (
            nps integer not null,
            coll integer not null,
            ctme float not null,
            out_file text not null
        );
        """
    )

class _Scanner:
    def accept(self, line_no: int, line: str) -> None:
        ...

@dataclass
class _DescriptionsItem:
    start_line: int
    description: list[str]


@dataclass
class _DescriptionsScanner(_Scanner):
    _wait_description: bool = True
    _start_line: int = 0
    _description: list[str] = field(default_factory=list)
    descriptions: list[_DescriptionsItem] = field(default_factory=list)

    def accept(self, line_no: int, line: str) -> None:
        if self._wait_description:
            if line.startswith("1   lost particle no."):
                self._start_line = line_no + 1
                self._description.append(line)
                self._wait_description = False
        else:
            self._description.append(line)
            if len(self._description) > 15:
                self._wait_description = True
                self.descriptions.append(_DescriptionsItem(self._start_line, self._description))
                self._description = []


@dataclass
class _NpsScanner(_Scanner):
    nps: int = 0
    coll: int = 0
    ctme: float = 0.0

    def accept(self, line_no: int, line: str) -> None:
        match = NPS_COLL_CTME_RE.match(line)
        if match:
            self.nps = int(match.group("nps"))
            self.coll = int(match.group("coll"))
            self.ctme = float(match.group("ctme"))



@dataclass
class _Description:
    cell_fail: int
    surface: int
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
    lp_no = 9999 if lp_no_str == "***" else int(lp_no_str)

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
        surface = 0
        cell_fail = 0
        line2 = lines[2].strip()
        cell_in = int(line2.split(".")[0].rsplit(maxsplit=2)[-1])
        x, y, z = map(float, lines[5].split()[-3:])
        u, v, w = map(float, lines[6].split()[-3:])
    else:
        msg = f"Unknown lost particles spec first line: {lines[0]}"
        raise ParseError(msg)

    return _Description(cell_fail, surface, cell_in, x, y, z, u, v, w, lp_no, hist_no)


# noinspection PyTypeChecker
def _process_file(p: Path, cur: sq.Cursor) -> None:
    with  p.open("r") as fid:
        descriptions_scanner = _DescriptionsScanner()
        nps_scanner = _NpsScanner()
        for i, line in enumerate(fid.readlines()):
            descriptions_scanner.accept(i, line)
            nps_scanner.accept(i, line)
    _save_lost_particles_information(cur, descriptions_scanner,  p)
    _save_nps_information(cur, nps_scanner, p)

def _save_lost_particles_information(cur: Cursor, descriptions_scanner: _DescriptionsScanner, p: Path) -> None:
    out_file_name = str(p)
    details_path = Path("lp-details.txt")
    if not details_path.exists():
        LOG.info("Creating file lp-details.txt")
    with details_path.open("a") as fid:
        for item in descriptions_scanner.descriptions:
            lines = item.description
            print("-" * 20, file=fid)
            for line in lines:
                print(line, file=fid, end="")
    for item in descriptions_scanner.descriptions:
        lines = item.description
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
            msg = f"Error parsing {p}: {item.start_line}"
            raise ParseError(msg) from ex

def _save_nps_information(cur: Cursor, nps_scanner: _NpsScanner, p: Path) -> None:
    out_file_name = str(p)
    if nps_scanner.ctme > 0:
        cur.execute(
                """
                    insert into nps_coll_ctme (
                        nps, coll, ctme, out_file
                    )
                    values (?,?,?,?)
                """,
            (nps_scanner.nps, nps_scanner.coll, nps_scanner.ctme, out_file_name)
            )
    else:
        LOG.warning("No NPS found in %s", out_file_name)


# noinspection PyTypeChecker
def _analyze(db) -> None:
    with sq.connect(db) as con:
        cur = con.cursor()
        total_lp = cur.execute(
            """
            select
                count(*)
            from
                lost_particles
            """
        ).fetchone()[0]
        rec = cur.execute(
            """
            select
                sum(nps) as nps, sum(ctme) as ctme
            from (
                select max(nps) as nps, max(ctme) as ctme
                from nps_coll_ctme
                group by out_file
            )
            """
        ).fetchone()
        nps, ctme = rec
        LOG.info("Total nps: %d (%.3g)", nps, nps)
        LOG.info("Total ctme: %.3g (%.3g hours)", ctme, ctme/3600)
        LOG.info("NPS/hour: %.3g", nps*3600/ctme)
        if total_lp:
            LOG.info("Total lost particles: %d", total_lp)
            if nps > 0:
                LOG.info("LPR: %.2g", total_lp/nps)
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
            with Path("lp-cell-fails-count.csv").open("w") as fid:
                for t in cell_fail_counts:
                    print(*t, sep=",", file=fid)
            LOG.info("Created file lp-cell-fails-count.csv")

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
            with Path("lp-coordinates.csv").open("w") as fid:
                for t in lost_coordinates:
                    print(*t, sep=",", file=fid)
            LOG.info("Created file lp-coordinates.csv")

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
            comin_path = Path("lp-comin")
            if comin_path.exists():
                LOG.info("Using existing 'comin' template %s", comin_path)
                comin_text = comin_path.read_text()
                comin_lines = comin_text.split("\n")
                comin_lines[0] = origin_text
                new_comin_text = "\n".join(comin_lines)
            else:
                LOG.info("Creating 'com' file %s", comin_path)
                new_comin_text = origin_text[:-1]
            with comin_path.open("w") as fid:
                print(new_comin_text, file=fid)
            LOG.info("Created file comin")
        else:
            LOG.info("No lost particles found")



def _collect_lost_particles(db: str) -> bool:
    files = _collect_files()
    if not files:
        return False
    LOG.info("%d files to process", len(files))
    is_old_db = Path(db).exists()
    with sq.connect(db) as con:
        cur = con.cursor()
        if is_old_db:
            LOG.info("Using existing database %s", db)
        else:
            LOG.info("Initializing database %s", db)
            setup_db(cur)
        for f in files:
            LOG.debug("Processing file %s", f)
            _process_file(f, cur)
    return True


def _collect_files() -> list[Path]:
    args = sys.argv[1:]
    return  [Path(a) for a in args] if args  else list(Path.cwd().glob("*.o"))


def main() -> None:
    """Workflow implementation."""
    logging.basicConfig(
        level=logging.INFO,
        filename="lp.log",
        filemode="a",
        format="%(asctime)s %(levelname)-9s %(message)s",
        datefmt="%Y-%d-%m %H:%M:%S",
    )
    LOG.info("extract-lost-particles, v%s", __version__)
    LOG.info("python version: %s", sys.version)

    db = "lp.sqlite"
    if _collect_lost_particles(db):
        _analyze(db)
    else:
        LOG.warning("Files not found")


if __name__ == "__main__":
    main()
