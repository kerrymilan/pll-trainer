# Rubik's Cube PLL Trainer

## Usage

```
usage: Find permutations of PLL algorithms that return the cube to a solved 
       state. If neither '--anki' or '--trainer' is specified, print all 
       identified sequences and their patterns' respective steps.

positional arguments:
  algorithms            Override the list of algorithms that will be tested.
                        If not specified, use all algorithms found in
                        ./pll.json

optional arguments:
  -h, --help            show this help message and exit
  -d MAX_DEPTH, --max-depth MAX_DEPTH
                        Set maximum recursion depth (default: 4)
  -a, --anki            Print all identified patterns in Anki's flash card
                        format
  -s SEARCH [SEARCH ...], --search SEARCH [SEARCH ...]
                        Only include sequences that use at least one of the
                        specified patterns
  -t, --trainer         Pick a random sequence and present the steps one by
                        one. Calculate time to solve each step, as well as
                        total time and average time per step. Advance from one
                        step to the next by pressing any key
  -v [VERBOSITY]        Set log level. Accepted up to 3 times (e.g. -vvv)
```

## Permutations

This script identifies permutations of PLL algorithms that return the cube to a
solved state. For example, applying algorithm 'T' followed by 'H' to a solved
cube will position the last layer such that executing 'F' solves the cube. This
is true for any order of T, H, and F:

```
F -> H -> T
F -> T -> H
H -> F -> T
H -> T -> F
T -> F -> H
T -> H -> F
```

## Output

The purpose of this script is to find these patterns given a list of algorithms
and filter criteria. It does so by recursively chaining together patterns up to
the specified maximum depth, then analyzing the cube to see if it has been
solved. It will then print the identified sequences in one of the following 
formats:

```
# Standard
F -> T -> H
F  - R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)
T  - (R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')
H  - (M2' U) (M2' U2) (M2' U) M2'

H -> F -> T
H  - (M2' U) (M2' U2) (M2' U) M2'
F  - R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)
T  - (R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')

H -> T -> F
H  - (M2' U) (M2' U2) (M2' U) M2'
T  - (R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')
F  - R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)

T -> H -> F
T  - (R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')
H  - (M2' U) (M2' U2) (M2' U) M2'
F  - R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)

T -> F -> H
T  - (R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')
F  - R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)
H  - (M2' U) (M2' U2) (M2' U) M2'

F -> H -> T
F  - R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)
H  - (M2' U) (M2' U2) (M2' U) M2'
T  - (R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')

# Anki Flash Cards
H -> T -> _,<div>(M2' U) (M2' U2) (M2' U) M2'</div><div>(R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')</div><div>R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)</div>,H T F
T -> H -> _,<div>(R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')</div><div>(M2' U) (M2' U2) (M2' U) M2'</div><div>R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)</div>,T H F
F -> T -> _,<div>R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)</div><div>(R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')</div><div>(M2' U) (M2' U2) (M2' U) M2'</div>,F T H
F -> H -> _,<div>R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)</div><div>(M2' U) (M2' U2) (M2' U) M2'</div><div>(R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')</div>,F H T
T -> F -> _,<div>(R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')</div><div>R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)</div><div>(M2' U) (M2' U2) (M2' U) M2'</div>,T F H
H -> F -> _,<div>(M2' U) (M2' U2) (M2' U) M2'</div><div>R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)</div><div>(R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')</div>,H F T
```

The output of 'Anki' mode (`-a` or `--anki`) can be imported into Anki's desktop
app, which can be downloaded from [apps.ankiweb.net](https://apps.ankiweb.net/).
Optionally, 'Trainer' mode (`-t` or `--trainer`) will randomly select a pattern
and display the steps one at a time, counting the time to solve each step. The
last step in this mode is masked and must be identified by analyzing the state
of the cube.

## Algorithms

The algorithms included in `pll.json` are listed below. These can be modified as
desired.

```
Aa: x (R' U R') D2 (R U' R') D2 R2
Ab: x R2 D2 (R U R') D2 (R U' R)
E : x' (R U') (R' D) (R U R' D') (R U R' D) (R U') (R' D')
F : R' U' F' (R U R' U') (R' F) (R2 U') (R' U' R U) (R' U R)
Ga: (R2' Uw) (R' U R' U' R Uw') R2' y' (R' U R)
Gb: (R' U' R) y (R2' Uw R' U) (R U' R Uw' R2')
Gd: (R U R') y' (R2' Uw' R U') (R' U R' Uw R2)
H : (M2' U) (M2' U2) (M2' U) M2'
Ja: (R' U L') U2 (R U' R') U2 (L R U')
Jb: (R U R' F') (R U R' U') (R' F) (R2 U') (R' U')
Ra: (R U R' F') (R U2 R' U2) (R' F) (R U R U2) (R' U')
Rb: (R' U2) (R U2) (R' F R U R' U') (R' F' R2 U')
T : (R U R' U') (R' F) (R2 U') (R' U' R U) (R' F')
Ua: (R U' R U) (R U) (R U') (R' U' R2)
Ub: (R2 U) (R U R' U') (R' U') (R' U R')
Y : (F R U') (R' U' R U) (R' F') (R U R' U') (R' F R F')
Z : (M2' U) (M2' U) (M' U2) (M2' U2) (M' U2)
# Not yet implemented: Na, Nb, Gc, V
```
