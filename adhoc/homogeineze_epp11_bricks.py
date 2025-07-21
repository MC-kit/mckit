import typing as tp

import sys

from pathlib import Path

import mckit as mk

universes_to_process = [97, 98, 99]


def actual_volume_97():
    # 189895 PX 869.412
    # 189896 PX 906.801
    # 189897 PY -2.8027
    # 189898 PY  2.8027
    # 189899 PZ -2.8027
    # 189900 PZ  2.8027
    dx = -869.412 + 906.801
    dy = 2.8027 + 2.8027
    dz = 2.8027 + 2.8027
    return dx * dy * dz


def get_path(universe_name: int) -> Path:
    return Path(f"u{universe_name:d}.i")


def load_universe(universe_name: int) -> mk.Universe:
    universe_path = get_path(universe_name)
    assert universe_path.exists()
    universe = mk.read_mcnp(universe_path)
    return universe


def process_universe(universe_name: int, min_volume=1e-3, out=sys.stdout) -> tp.NoReturn:
    universe = load_universe(universe_name)
    cell: mk.Body = universe[0]
    volume0 = cell.shape.volume(min_volume=min_volume)
    print(f"Volume of the root cell: {volume0}")
    if universe_name == 97:
        print(f"MCNP volume: {actual_volume_97()}")
    universe.apply_fill(cell.name(), name_rule="keep")
    universe.simplify(min_volume=0.1)
    total_volume = 0.0
    material_index = {}
    material_volume_map = {}
    for cell in universe:
        material = cell.material()
        volume = cell.shape.volume(min_volume=min_volume)
        total_volume += volume
        if material is not None:
            material_name = (
                material.composition.name()
            )  # TODO dvp: reverse dependency Composition-Material?
            if material_name not in material_index:
                material_index[material_name] = material
            material_volume = material_volume_map.get(material_name, 0.0) + volume
            material_volume_map[material_name] = material_volume
    print(f"Total volume: {total_volume}")
    material_volume_fractions = []
    for k, v in material_volume_map.items():
        material_volume_fractions.append((material_index[k], v / volume0))
    mixed_material = mk.Material.mixture(*material_volume_fractions, fraction_type="volume")
    composition = mixed_material.composition
    composition.rename(universe_name)
    print(
        f"""c {'='*20}
c Material for filler #{universe_name}
c Density {mixed_material.density:.3g}, g/ccm
c
c Mixture:
c""",
        file=out,
    )
    for m, f in material_volume_fractions:
        print(f"c m{m.composition.name()} {f*100:.1f} vol%", file=out)
    print(f"c\nc {'-'*20}", file=out)
    print(mixed_material.composition.mcnp_repr(), file=out)


def main():
    with open("mixed_materials.txt", "w") as fid:
        for universe_name in universes_to_process:
            process_universe(universe_name, min_volume=1e-3, out=fid)


if __name__ == "__main__":
    main()
