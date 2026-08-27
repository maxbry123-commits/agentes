# G5 canonical source record

- Original p01_* … p12_* source modules were not present in the repository search.
- Director authorization for this recovery loop permits a derived modularization of the existing canonical runner.
- Canonical implementation source: `extensions/wordflow/engine/code_path_runner.py`
- Canonical pipeline source: `extensions/wordflow/engine/programming_pipeline.py`
- Rule: do not modify either canonical source in G5.
- Derived stages must call/reuse existing behavior and must not duplicate `goal_lock`, `cognitive_loop`, or `evidence_packet`.
- This file is provenance evidence, not a fabricated p01–p12 source snapshot.
