# TAREA PENDIENTE - YAIWES SECRET BANK EN HUGGING FACE (2026-09-21, orden del Director)

Estado: PENDIENTE. Va despues de la prioridad actual (crear los 4 agentes).

Diseno pedido:
1. HF Storage Bucket = solo disco. YAIWES controla el cifrado.
2. Contrasena maestra -> Argon2id -> clave maestra solo en memoria.
3. Cada clave de API cifrada con AES-256-GCM.
4. Import/export con SOPS + age. Evolucion futura: OpenBao.

En HF se guarda: vault.enc, vault.meta.json, audit.jsonl, backups.
No se guarda: claves en claro ni la contrasena maestra.

Reusar: vault.py, session.py y broker.py del router (hoy scrypt; cambiar a Argon2id).
Ya en HF storage de COMAND-CENTER-1: secret_bank con el banco NVIDIA y vault.db.

Bloqueo: el entorno de Claude no llega a huggingface.co; el computo en HF se lanza con workflows del repo del router.
