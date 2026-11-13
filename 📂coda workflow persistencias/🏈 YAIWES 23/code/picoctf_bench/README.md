# HackSynth PicoCTF Benchmark

This is a collection of solver scripts and a benchmark json file for PicoCTF. The scripts are intended to be used for benchmarking the cybersecurity performance of various Large Language Models and solver systems.

## Running the solvers
The solver scripts are implemented to run inside of a docker container.

- Build the docker image with the following:
  ```
  docker build -t pico-solver .
  ```

- Run the solver with the following (run this in the same directory as the `benchmark.json` file):
  ```
  docker run -it --rm -v `pwd`:/app pico-solver
  ```

- Use the following if having problems with networking in the container:
  ```
  docker build --network=host -t pico-solver . && docker run --network=host -it --rm -v `pwd`:/app pico-solver
  ```

- After the script has finished running, you will find the solution file at `benchmark_solved.json`.
- You can benchmark HackSynth on the created solution file with the following command:
  ```
  python run_bench.py -b benchmark_solved.json -c config.json
  ```
  All `config.json` files used for the measurements in the paper are available in the configs folder.

## Dependencies
OS package:
- upx
- exiftool
- tshark
- zsteg
- git
- strings
- awk
- gzip
- binwalk
- unzip
- curl
- steghide
- apktool
- sleuthkit
- tesseract
- netcat
- gdb

Python:
- gmpy2
- PIL
- pytesseract
- itsdangerous
- flask
- pwntools
- pymupdf
- frontend
- tools (pytils)

Online services used:
- http://www.factordb.com
- https://quipqiup.com
