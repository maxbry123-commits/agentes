name: Research Download Chain FINAL
run-name: Research Download Chain FINAL • ${{ github.event_name }} • ${{ github.sha }}

on:
  workflow_dispatch:

permissions:
  contents: write

env:
  GIT_LFS_SKIP_SMUDGE: "1"
  GIT_LFS_SKIP_PUSH: "1"
  GIT_LFS_SKIP_DOWNLOAD: "1"
  GIT_TERMINAL_PROMPT: "0"

concurrency:
  group: research-download-chain-final
  cancel-in-progress: true

jobs:
  download-20-in-queue:
    name: Download 20 repos sequentially
    runs-on: ubuntu-latest
    timeout-minutes: 330
    steps:
      - name: Checkout main
        uses: actions/checkout@v4
        with:
          fetch-depth: 1
          lfs: false
      - name: Execute deterministic download chain
        shell: bash
        env:
          GIT_LFS_SKIP_SMUDGE: "1"
          GIT_LFS_SKIP_PUSH: "1"
          GIT_TERMINAL_PROMPT: "0"
        run: |
          set -euo pipefail
          git config --global filter.lfs.smudge ''
          git config --global filter.lfs.clean ''
          git config --global filter.lfs.process ''
          git config --global filter.lfs.required false
          git config --global core.compression 0
          python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'
