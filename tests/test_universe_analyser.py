from __future__ import annotations

from io import StringIO

from mckit.parser import from_file
from mckit.universe import UniverseAnalyser
from mckit.utils import path_resolver

cli_data = path_resolver("tests.cli")


def test_test_universe_analyser():
    universe_path = cli_data("data/shared_surface.mcnp")
    assert universe_path.exists()
    universe = from_file(universe_path).universe
    analyzer = UniverseAnalyser(universe)
    assert not analyzer.cell_duplicates
    assert not analyzer.surface_duplicates
    assert analyzer.surface_to_universe_map
    assert analyzer.surface_to_universe_map[1] == {
        0: 3,
        1: 1,
    }, "The surface 1 occurs 3 times in universes 0 and once in universe 1"
    assert analyzer.we_are_all_clear()
    out = StringIO()
    analyzer.print_duplicates_map(stream=out)
    assert "surface 1 occurs" in out.getvalue()
