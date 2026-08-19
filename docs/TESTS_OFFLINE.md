# Tests offline — T47

Desde la raíz del repo (o `extensions/`):

```bash
cd extensions
python -m unittest discover -s wordflow_kernel/tests -p 'test_*.py' -v
python -m unittest discover -s wordflow/tests -p 'test_*.py' -v
python -m unittest discover -s maxbry_loop/tests -p 'test_*.py' -v
```

Smokes puntuales post-gapfix R3:

```bash
python -m unittest wordflow_kernel.tests.test_reception_ingest wordflow_kernel.tests.test_vk01_models maxbry_loop.tests.test_code_path_bridge -v
```

CI: `.github/workflows/test-wordflow-code-path.yml`

No secrets. No vendor LLM. C-19 Fake/BLOCK no es PASS.
