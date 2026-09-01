# auditoria/ — evidencia forense de despliegue

Conserva para verificación cruzada (sin contaminar wordflow/):

1. versión exacta desplegada
2. commit SHA
3. hashes / checksums (`checksums.yaml`)
4. manifiesto del despliegue
5. schema utilizado
6. resultado de validación (`verification.yaml`)
7. correspondencia entre YAML y código
8. evidencia de qué se ejecutó
9. fecha / versión de la ejecución

Los workflows ejecutables siguen en `.github/workflows/`.
