# Kubernetes Deployment Guide

> Deploy Cognithor on Kubernetes with GPU support, persistent storage, and health probes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Namespace](#namespace)
- [ConfigMap](#configmap)
- [PersistentVolumeClaim](#persistentvolumeclaim)
- [Deployment](#deployment)
- [Service](#service)
- [Ingress](#ingress)
- [GPU Node Selector](#gpu-node-selector)
- [Health and Readiness Probes](#health-and-readiness-probes)
- [Ollama Sidecar](#ollama-sidecar)
- [Complete Manifest](#complete-manifest)
- [Operations](#operations)

---

## Prerequisites

- Kubernetes 1.26+
- NVIDIA GPU Operator installed (for GPU workloads)
- `nvidia.com/gpu` resource available on at least one node
- Container image built and pushed to your registry
- `kubectl` configured for your cluster

---

## Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cognithor
```

---

## ConfigMap

Store `config.yaml` as a ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cognithor-config
  namespace: cognithor
data:
  config.yaml: |
    language: "en"
    models:
      planner:
        name: qwen3:32b
        context_window: 32768
      executor:
        name: qwen3:8b
        context_window: 32768
      embedding:
        name: qwen3-embedding:0.6b
        context_window: 8192
        embedding_dimensions: 1024
    ollama:
      base_url: "http://localhost:11434"
      timeout_seconds: 120
      keep_alive: "30m"
    planner:
      max_iterations: 25
    security:
      allowed_paths:
        - /data/cognithor
    gepa:
      enabled: true
      evolution_interval_hours: 6
      min_traces_for_proposal: 10
```

---

## PersistentVolumeClaim

Cognithor stores data in `~/.jarvis/` (configurable via `JARVIS_HOME`). Use a PVC for persistence:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cognithor-data
  namespace: cognithor
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard    # Adjust for your cluster
  resources:
    requests:
      storage: 20Gi             # Memory DB, logs, FAISS index, traces
```

---

## Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cognithor
  namespace: cognithor
  labels:
    app: cognithor
spec:
  replicas: 1                   # Single replica (stateful, not horizontally scalable)
  selector:
    matchLabels:
      app: cognithor
  template:
    metadata:
      labels:
        app: cognithor
    spec:
      # GPU scheduling
      nodeSelector:
        nvidia.com/gpu.present: "true"
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule

      containers:
        # ── Cognithor Application ──
        - name: cognithor
          image: your-registry/cognithor:latest
          command: ["python", "-m", "jarvis", "--no-cli", "--api-port", "8741"]
          ports:
            - containerPort: 8741
              name: http
              protocol: TCP
          env:
            - name: JARVIS_HOME
              value: /data/cognithor
            - name: JARVIS_CONFIG
              value: /config/config.yaml
            - name: OLLAMA_HOST
              value: "http://localhost:11434"
            - name: PYTHONUNBUFFERED
              value: "1"
            # Optional: API token (auto-generated if not set)
            # - name: JARVIS_API_TOKEN
            #   valueFrom:
            #     secretKeyRef:
            #       name: cognithor-secrets
            #       key: api-token
          volumeMounts:
            - name: data
              mountPath: /data/cognithor
            - name: config
              mountPath: /config
              readOnly: true
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
            limits:
              memory: "4Gi"
              cpu: "4"

          # Health probes
          livenessProbe:
            httpGet:
              path: /api/v1/health
              port: 8741
            initialDelaySeconds: 30
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /api/v1/health
              port: 8741
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /api/v1/health
              port: 8741
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 30    # Up to 150s for model loading

        # ── Ollama Sidecar ──
        - name: ollama
          image: ollama/ollama:latest
          ports:
            - containerPort: 11434
              name: ollama
              protocol: TCP
          volumeMounts:
            - name: ollama-models
              mountPath: /root/.ollama
          resources:
            requests:
              memory: "4Gi"
              nvidia.com/gpu: "1"
            limits:
              memory: "32Gi"
              nvidia.com/gpu: "1"
          livenessProbe:
            httpGet:
              path: /
              port: 11434
            initialDelaySeconds: 10
            periodSeconds: 30

      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: cognithor-data
        - name: config
          configMap:
            name: cognithor-config
        - name: ollama-models
          persistentVolumeClaim:
            claimName: ollama-models

      # Graceful shutdown (save state before termination)
      terminationGracePeriodSeconds: 60
```

### Ollama Models PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-models
  namespace: cognithor
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 50Gi              # Models can be large (32b ~ 20GB)
```

---

## Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: cognithor
  namespace: cognithor
  labels:
    app: cognithor
spec:
  type: ClusterIP
  selector:
    app: cognithor
  ports:
    - name: http
      port: 8741
      targetPort: 8741
      protocol: TCP
```

---

## Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cognithor
  namespace: cognithor
  annotations:
    # Adjust for your ingress controller
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    # WebSocket support
    nginx.ingress.kubernetes.io/proxy-http-version: "1.1"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
    # TLS
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - cognithor.example.com
      secretName: cognithor-tls
  rules:
    - host: cognithor.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: cognithor
                port:
                  number: 8741
```

**Important:** WebSocket connections (`/ws`) require the `Upgrade` headers configured above. Without them, the chat interface will fail to connect.

---

## GPU Node Selector

### Single GPU

The deployment above requests 1 GPU via `nvidia.com/gpu: "1"`. This is assigned to the Ollama sidecar.

### Multi-GPU (Large Models)

For models requiring multiple GPUs (e.g., qwen3:32b on smaller GPUs), use:

```yaml
resources:
  limits:
    nvidia.com/gpu: "2"
```

And configure Ollama to use multiple GPUs:

```yaml
env:
  - name: CUDA_VISIBLE_DEVICES
    value: "0,1"
```

### Node Affinity (Specific GPU Types)

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: nvidia.com/gpu.product
              operator: In
              values:
                - NVIDIA-A100-SXM4-80GB
                - NVIDIA-A100-SXM4-40GB
```

---

## Health and Readiness Probes

| Probe | Endpoint | Purpose |
|-------|----------|---------|
| **Liveness** | `GET /api/v1/health` | Restart pod if unresponsive |
| **Readiness** | `GET /api/v1/health` | Remove from Service endpoints until ready |
| **Startup** | `GET /api/v1/health` | Allow slow startup (model loading) without killing pod |

The startup probe allows up to 150 seconds (30 attempts x 5s) for initial model loading. Adjust `failureThreshold` if your models are very large.

---

## Operations

### Pull Models (Init Container)

To pre-pull Ollama models before starting Cognithor, add an init container:

```yaml
initContainers:
  - name: pull-models
    image: ollama/ollama:latest
    command:
      - /bin/sh
      - -c
      - |
        ollama pull qwen3:32b
        ollama pull qwen3:8b
        ollama pull qwen3-embedding:0.6b
    volumeMounts:
      - name: ollama-models
        mountPath: /root/.ollama
    resources:
      limits:
        nvidia.com/gpu: "1"
```

### Scaling

Cognithor is stateful (SQLite databases, in-memory sessions). Horizontal scaling is **not supported** with a single PVC. For multi-replica deployments:

1. Use PostgreSQL for shared state (enable `[postgresql]` extra)
2. Use a shared filesystem (NFS, CephFS) for the data directory
3. Use sticky sessions at the Ingress level

### Logs

```bash
# Application logs
kubectl logs -n cognithor deployment/cognithor -c cognithor -f

# Ollama logs
kubectl logs -n cognithor deployment/cognithor -c ollama -f
```

### Shell Access

```bash
kubectl exec -it -n cognithor deployment/cognithor -c cognithor -- /bin/bash
```

### Restart

```bash
kubectl rollout restart -n cognithor deployment/cognithor
```
