# HackSynth OverTheWire Benchmark

These are solver scripts and benchmark json files for OverTheWire challenges. The scripts are intended to be used for benchmarking the cybersecurity performance of various Large Language Models and solver systems.

## Running the solvers

- Ensure that all dependencies are installed on your system
- Running `python {name}_solver.py` creates the solutions for a single benchmark, into the `{name}_solved.json`, where `{name}` is the name of the specific wargame
- Running the `run_solvers.sh` script creates all the solutions, and combines them into a single `combined_solved.json`
- After the solution file has been created, you can benchmark HackSynth on it with the following command:
  ```
  python run_bench.py -b combined_solved.json -c config.json
  ```
  All `config.json` files used for the measurements in the paper are available in the configs folder.

## Bandit dependencies
Python:
- pwntools

## Natas dependencies
OS package:
- php

Python:
- pwntools
- requests
- urllib
- base64

## Leviathan dependencies
Python:
- pwntools

## Krypton dependencies
Python:
- pwntools
- requests

Online services used:
- https://quipqiup.com
- https://www.guballa.de/vigenere-solver
