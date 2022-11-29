#!/usr/bin/env python3
"""
A script to generate a random cubic unit cell of carbon atoms.

# Usage:
>>> ./generate_structure.py N=200 density=3.5 
prints N-200-density-3.5-id-1
output found in structures/N-200-density-3.5-id-1.data file

repeated usage bumps the id
>>> ./generate_structure.py N=200 density=3.5 
N-200-density-3.5-id-2

pass hard_sphere_r to change the hard sphere constraint
>>> ./generate_structure.py N=200 density=3.5 hard_sphere_r=0.7
N-200-density-3.5-hard_sphere_r-0.7-id-1

pass arbitrary other kwargs as identifiers
>>> ./generate_structure.py N=200 density=3.5 tag=test 
N-200-density-3.5-tag-test-id-1
"""

import os
import sys
from ase import Atoms
from ase.io import write
import numpy as np


def lattice_parameter(N: int, density: float):
    """
    lattice parameter for a cubic unit cell containing
    `N` carbon atoms and with `density` in gcm^-3
    """
    u = 1.66054 * 10**(-30)
    c_mass = 12
    cell_vol = (c_mass*u*N)/density    # in m^3
    return (cell_vol**(1/3)) * 10**10  # in Angstrom


def generate_structure(
    N: int, density: float, hard_sphere_r: float = 0.5, **kwargs
):
    """
    Generate a random structure.

    Create a unit cell with N atoms all at (0, 0, 0).
    Leave the first atom where it is.
    Move the remaining atoms so that no atoms intersect each other using
        a hard sphere constraint.
    Shift all atoms a random vector so that spurious (0, 0, 0) dissapears.
    """

    a = lattice_parameter(N, density)
    structure = Atoms(f"C{N}", cell=[a, a, a, 90, 90, 90], pbc=True)

    i = 1
    while i < N:
        position = np.random.rand(3) * a
        structure.positions[i] = position

        for j in range(i):  # all other atoms in their final positions
            if structure.get_distance(i, j) < 2 * hard_sphere_r:
                # failed to move atom to acceptable spot
                structure.positions[i] = [0, 0, 0]
                i -= 1
                break
        i += 1

    # randomly displace all atoms by the same vector
    shift = np.random.rand(3) * a
    structure.positions += shift
    structure.wrap()

    return structure


def process_kwargs():
    try:
        kwargs = dict(map(split_on("="), sys.argv[1:]))
    except ValueError:
        print("Unable to parse script kwargs. "
              "Ensure that all options are passed in the form 'key=value'.")
        exit(1)

    usage = """\
        Usage is `./generate_structure.py N=<N> density=<density>`
        e.g. `./generate_structure.py N=200 density=1.5`"""
    assert all(k in kwargs for k in ("N", "density")), usage

    kwargs["N"] = int(kwargs['N'])
    kwargs['density'] = round(float(kwargs['density']), 3)

    if "hard_sphere_r" in kwargs:
        kwargs["hard_sphere_r"] = round(float(kwargs['hard_sphere_r']), 3)

    return kwargs


def split_on(thing): return lambda string: string.split(thing)


if __name__ == "__main__":
    kwargs = process_kwargs()
    structure = generate_structure(**kwargs)

    os.makedirs("./structures", exist_ok=True)

    v = 1
    name = "-".join(f"{k}-{kwargs[k]}" for k in sorted(kwargs)) + f"-id-{v}"
    while os.path.exists("./structures/" + name + ".data"):
        v += 1
        name = "-".join(f"{k}-{kwargs[k]}" for k in sorted(kwargs)
                        ) + f"-id-{v}"

    print(name)

    write("./structures/" + name + ".data", structure,
          format="lammps-data", atom_style="atomic")
