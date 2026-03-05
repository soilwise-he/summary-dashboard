### Superset + Keycloak

Apache Superset with Keycloak OAuth2 authentication in Docker.

### Quick Start

```bash
docker-compose up -d
```

Access:

- Superset: http://localhost:8088
- Keycloak: http://localhost:XXXX
- Login: `admin` / `admin`

### Architecture

```
Browser → Superset:8088 ↔ Keycloak:XXXX
    ↓              
    Redis      
```

## How It Works

**Authentication**: OAuth2 flow between Superset and Keycloak

- `superset_config.py` configures OAuth provider and role mapping
- `realm-import/*.json` defines Keycloak realm, users, and client

**Sessions**: Stored in Redis

**Roles**: Keycloak roles → Superset permissions

- `admin`/`realm-admin` → Admin
- Others → Gamma (basic user)

**URLs**:

- Internal (containers): `keycloak:8080`
- External (browser): `localhost:8090`

## Key Files

- `docker-compose.yml` - Services: Superset, Redis
- `superset_config.py` - OAuth config, security manager, session/cache setup
- `realm-import/*.json` - Keycloak realm with users and client config
- `Dockerfile` - Superset image with dependencies

## Configuration Highlights

**Superset (`superset_config.py`)**:

- OAuth provider points to Keycloak endpoints
- CustomSecurityManager maps Keycloak roles to Superset
- Redis for sessions and cache
- SQLite for metadata

**Keycloak (`realm-import`)**:

- Client: `superset` with secret
- Redirect URIs: `http://localhost:8088/*`
- Protocol mapper: exposes roles in JWT token

**Docker Compose**:

- Network: All containers on `app-network`
- Health checks ensure services start in order
- Volume mounts for configs and persistence

## Check services

docker-compose ps

# View logs

docker-compose logs -f superset
docker-compose logs -f keycloak

# Run Kubernetes Services
# Superset Dashboard — Deployment Guide

## 🚀 First-Time Setup

```powershell
# 1. Start Minikube (Docker Desktop must be running)
minikube start

# 2. Build & load image into Minikube
docker build -t superset:latest .
minikube image load superset:latest

# 3. Apply manifests
cd k8_manifests
kubectl apply -f configmap.yaml
kubectl apply -f superset-config.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f keycloak.yaml
kubectl apply -f superset.yaml

# 4. Watch pods (wait until all Running)
kubectl get pods -w

# 5. Expose services — run in a separate terminal
minikube tunnel
```

Superset → `http://localhost:8088` | Keycloak → `http://localhost:8090`

---

## 🔄 Teardown & Redeploy

```powershell
# Delete
kubectl delete -f env-configmap.yaml -f superset-config.yaml -f keycloak.yaml -f superset.yaml -f redis.yaml -f postgres.yaml

# Redeploy
kubectl apply -f env-configmap.yaml -f superset-config.yaml -f postgres.yaml -f redis.yaml -f keycloak.yaml -f superset.yaml
```

---

## ☁️ AWS — Values to Update

| File | Key | Value |
|------|-----|-------|
| `env-configmap.yaml` | `KEYCLOAK_EXTERNAL_URL` | `http://<keycloak-elb-dns>:8090` |
| `env-configmap.yaml` | `SUPERSET_EXTERNAL_URL` | `http://<superset-elb-dns>:8088` |
| `superset-config.yaml` | `OVERWRITE_REDIRECT_URI` | `http://<superset-elb-dns>:8088/oauth-authorized/keycloak` |
| `keycloak.yaml` | `KC_HOSTNAME` | `<keycloak-elb-dns>` |
| `keycloak.yaml` | `redirectUris` | `http://<superset-elb-dns>:8088/*` |

> No `minikube tunnel` needed on AWS — ELBs are provisioned automatically.  
> Internal URLs (Redis, Postgres, `KEYCLOAK_INTERNAL_URL`) never change.


# Kubernetes Pods Flowchart

```mermaid
flowchart TB
    Browser["🌐 Browser\nlocalhost:8088 / localhost:8090"]

    subgraph Tunnel["minikube tunnel (Windows)"]
        LB1["LoadBalancer\n127.0.0.1:8088"]
        LB2["LoadBalancer\n127.0.0.1:8090"]
    end

    subgraph Cluster["Kubernetes Cluster"]
        subgraph Superset["superset pod"]
            S["Superset\n:8088"]
        end

        subgraph Keycloak["keycloak pod"]
            K["Keycloak\n:8080"]
        end

        subgraph Redis["redis pod"]
            R["Redis\n:6379"]
        end

        subgraph Postgres["postgres pod"]
            P["PostgreSQL\n:5432"]
        end
    end

    Browser -->|"① click login"| LB1
    LB1 --> S
    S -->|"② redirect to Keycloak\n(authorize_url)"| Browser
    Browser -->|"③ login form"| LB2
    LB2 --> K
    K -->|"④ redirect back with code"| Browser
    Browser -->|"⑤ /oauth-authorized/keycloak"| LB1
    LB1 --> S
    S -->|"⑥ token exchange\nkeycloak:8090"| K
    S -->|"⑦ userinfo\nkeycloak:8090"| K
    K -->|"stores sessions"| P
    S -->|"cache / sessions"| R
```

# Moving to AWS

ELB DNS names are assigned automatically — no `minikube tunnel` needed. Only update these values:

| File | What to change |
|------|---------------|
| `env-configmap.yaml` | `KEYCLOAK_EXTERNAL_URL` and `SUPERSET_EXTERNAL_URL` — change `http` → `https` |
| `superset-config.yaml` | `OVERWRITE_REDIRECT_URI` — change `http` → `https`, set `ENABLE_PROXY_FIX = True`, `SESSION_COOKIE_SECURE = True` |
| `keycloak.yaml` | `KC_HOSTNAME` to ELB DNS, `redirectUris` + `webOrigins` to `https`, set `KC_HOSTNAME_STRICT_HTTPS: "true"` and `KC_HTTP_ENABLED: "false"` |

Everything else (internal Redis, Postgres, Keycloak pod-to-pod URLs) stays the same.