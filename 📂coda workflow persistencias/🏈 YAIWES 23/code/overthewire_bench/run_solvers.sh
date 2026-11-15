#!/bin/bash

# Run each solver script in order
echo "Running Bandit Solver..."
python bandit_solver.py

echo "Running Krypton Solver..."
python krypton_solver.py

echo "Running Leviathan Solver..."
python leviathan_solver.py

echo "Running Natas Solver..."
python natas_solver.py

# Combine the results
echo "Combining results..."
python combine.py

echo "All scripts executed successfully."
