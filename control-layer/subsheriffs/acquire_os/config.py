"""ACQUIRE-OS v1 — config / feature flags.

Dark launch (A7 F5): el módulo existe y está registrado en testing,
pero NINGÚN agente Wordflow lo invoca como nativo hasta que el Director
pase el flag a true y confirme gpg_key_id real.
"""

# Master switch — F5 dark launch
ACQUIRE_OS_ENABLED = False

# No auto-merge de PRs del Publisher (T-009)
AUTO_MERGE_IF_SHERIFF_PASS = False

# Límites GitHub (referencia; SIZE_ROUTER decide caso a caso)
GITHUB_FILE_HARD_LIMIT_BYTES = 100 * 1024 * 1024  # 100 MiB
GITHUB_PUSH_SOFT_LIMIT_BYTES = 2 * 1024 * 1024 * 1024  # ~2 GiB práctico

# TTL ficha en testing (días) antes de marcar stale
FICHA_TESTING_TTL_DAYS = 30

# Mission lock TTL (segundos)
MISSION_LOCK_TTL_SEG = 900
