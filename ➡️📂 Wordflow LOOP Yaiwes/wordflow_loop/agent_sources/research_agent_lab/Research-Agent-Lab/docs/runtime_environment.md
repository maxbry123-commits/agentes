# Runtime Environment

The project runtime is standardized on:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe
```

Use this interpreter for:

- Research Agent Lab workflow runs.
- Unit tests.
- Local paper parsing.
- `Intent-LED-mul-agent` debug training and evaluation.

Common commands:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 8
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main check-config --topic topics\intent_led_virat.json
```

Installed runtime additions:

- `pypdf` for local PDF full-text extraction.

API keys are still read from environment variables, not from tracked files.
