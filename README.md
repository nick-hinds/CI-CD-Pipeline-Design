# Python Kubernetes CI/CD Pipeline with kind

### Exercise time: ~2 hrs

A **production-ready, zero-setup** CI/CD pipeline for deploying Python web applications to Kubernetes using **kind (Kubernetes in Docker)**. Everything runs in GitHub Actions - no external clusters or cloud costs required!

## 🎯 Overview

This project provides a complete CI/CD pipeline that automatically builds, tests, scans, and deploys a Python FastAPI application to Kubernetes. It uses kind to create ephemeral Kubernetes clusters directly in GitHub Actions, eliminating the need for external infrastructure.

### Key Features

✅ **Zero External Dependencies** - Kubernetes runs entirely in GitHub Actions  
✅ **Complete CI/CD Pipeline** - 6 automated stages from code to deployment  
✅ **Multi-Environment** - Separate staging and production environments  
✅ **Security Scanning** - Code, dependency, and container image scanning with Trivy  
✅ **Approval Gates** - Manual approval required for production  
✅ **Git-Based Rollback** - Safe, auditable rollback strategy  
✅ **No Cloud Costs** - Completely free to run  
✅ **Production Ready** - Health checks, resource limits, monitoring hooks  

## 📋 Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Pipeline Stages](#pipeline-stages)
- [Rollback Strategy](#rollback-strategy)
- [Secrets Management](#secrets-management)
- [Testing Guide](#testing-guide)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture

### Pipeline Flow

```
Developer Push → Build & Test → Security Scan → Build Image → Scan Image
                                                                    ↓
                                                      develop branch? Yes → Deploy Staging
                                                                    ↓
                                                         main branch? Yes → ⏸ Approval Gate
                                                                    ↓
                                                              Deploy Production
```

### Deployment Environments

| Environment | Trigger | Approval | Replicas | Auto-Deploy |
|-------------|---------|----------|----------|-------------|
| **Staging** | Push to `develop` | None | 2 | ✅ Yes |
| **Production** | Push to `main` | Required | 2 | ❌ Manual |

---

## 🚀 Quick Start

### Step 1: Create GitHub Environments

1. Go to **Settings** → **Environments**
2. Create `staging` (no approval)
3. Create `production` (add yourself as reviewer)

### Step 2: Push Code

```bash
git add .
git commit -m "Add CI/CD pipeline"
git push origin main
```

### Step 3: Test Staging

```bash
git checkout -b develop
git push origin develop
# Watch auto-deployment in Actions tab
```

### Step 4: Deploy Production

```bash
git checkout main
git merge develop
git push origin main
# Approve in Actions tab when prompted
```

---

## 📊 Pipeline Stages

### Stage 1: Build and Test (1-2 min)
- Checkout code
- Setup Python 3.11
- Install dependencies
- Run linting (flake8, black, isort)
- Run pytest with coverage
- Generate version number

### Stage 2: Security Scanning - Code (30-45 sec)
- **Bandit:** Python security linter
- **Safety:** Dependency vulnerability check
- **Dependency Review:** (PR only)

### Stage 3: Build Docker Image (1-2 min)
- Multi-stage Docker build
- Test health endpoint
- Save as artifact

### Stage 4: Container Security Scanning (1-2 min)
- **Trivy:** Scan for vulnerabilities
  - OS packages
  - Python dependencies
  - Known CVEs
- Upload to GitHub Security tab
- Generate SARIF and JSON reports

### Stage 5: Deploy to Staging (3-4 min)
**Trigger:** Push to `develop`

- Create kind cluster
- Load image
- Apply Kubernetes manifests
- Run smoke tests (/health, /)
- Show logs

**Auto-deploys** - No approval needed

### Stage 6: Deploy to Production (4-5 min)
**Trigger:** Push to `main`

- Run all previous stages
- **⏸ Wait for manual approval**
- Create kind cluster
- Load image
- Apply manifests
- Run smoke tests (/health, /, /api/status)
- Performance checks
- Auto-rollback on failure

**Requires approval** from designated reviewers

---

## 🔄 Rollback Strategy

### Why Git-Based Rollback?

This pipeline uses **Git-based rollback** because kind creates ephemeral clusters with no deployment history.

**Traditional Kubernetes:**
```bash
kubectl rollout undo  # ❌ Doesn't work with kind
```

**Git-Based:**
```bash
git revert <commit>   # ✅ Works perfectly
git push origin main
```

### Method 1: Git Revert (Recommended)

**When:** Standard rollback for bad deployments

```bash
# Find problematic commit
git log --oneline -10

# Revert it
git revert abc1234

# Push to trigger redeployment
git push origin main  # or develop for staging
```

**Timeline:** 5-7 minutes (full pipeline)

### Method 2: Redeploy Previous Commit

**When:** Multiple bad commits

```bash
# Find last good commit
git log --oneline -10

# Create rollback branch
git checkout def5678
git checkout -b rollback-fix

# Push and create PR
git push origin rollback-fix
```

**Timeline:** 7-10 minutes (includes PR)

### Method 3: Emergency Reset (Caution!)

**When:** Critical production issue

```bash
# Find last good commit
git log --oneline

# Reset (DESTRUCTIVE!)
git reset --hard def5678
git push -f origin main

# ⚠️ Coordinate with team first!
```

**Timeline:** 5 minutes

### Rollback Decision Matrix

| Situation | Method | Timeline |
|-----------|--------|----------|
| Single bad commit | Git Revert | 5-7 min |
| Multiple bad commits | Redeploy Previous | 7-10 min |
| Critical issue | Emergency Reset | 5 min |

### Rollback Workflow

A rollback workflow is available for tracking:

1. **Actions** → **Rollback Deployment**
2. Select environment and provide reason
3. Workflow provides instructions
4. Execute git revert as shown above

### For Persistent Clusters

When migrating to real clusters (GKE/EKS/AKS):

```yaml
kubectl rollout undo deployment/python-app -n production
```

This will work with persistent clusters!

---

## 🔐 Secrets Management

### Current Implementation (kind)

**Required Secrets:** None!

Because kind runs in GitHub Actions, no external credentials needed.

**Optional:**
```
CODECOV_TOKEN - For coverage upload (optional)
```

### Why No Secrets?

1. **No External Clusters** - kind creates clusters in GitHub Actions
2. **No Cloud Credentials** - Runs locally in runner
3. **GitHub Auto-Auth** - Container registry access included

### Adding Application Secrets

If your app needs secrets (database, API keys):

#### 1. Create GitHub Secrets

**Settings** → **Secrets** → **Actions** → **New repository secret**

```
DATABASE_URL = postgresql://user:pass@host:5432/db
API_KEY = your-api-key
SECRET_KEY = your-secret-key
```

#### 2. Update Deployment Step

```yaml
- name: Create application secrets
  run: |
    kubectl create secret generic python-app-secrets \
      --from-literal=DATABASE_URL="${{ secrets.DATABASE_URL }}" \
      --from-literal=API_KEY="${{ secrets.API_KEY }}" \
      -n production
```

#### 3. Reference in Deployment

Update `k8s/deployment.yaml`:

```yaml
containers:
- name: python-app
  env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: python-app-secrets
        key: DATABASE_URL
```

### Production Secrets Strategy

For real Kubernetes clusters:

#### 1. GitHub Secrets (Cluster Access)

```
STAGING_KUBECONFIG - Base64 kubeconfig for staging
PRODUCTION_KUBECONFIG - Base64 kubeconfig for production
```

**Generate:**
```bash
kubectl config view --minify --raw > kubeconfig.yaml
cat kubeconfig.yaml | base64 > kubeconfig-base64.txt
# Add to GitHub Secrets
```

#### 2. Kubernetes Secrets (Application)

```bash
kubectl create secret generic python-app-secrets \
  --from-literal=database-url="postgresql://..." \
  -n production
```

#### 3. External Secrets Manager (Recommended)

**AWS Secrets Manager:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: python-app-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
  target:
    name: python-app-secrets
```

**HashiCorp Vault:**
```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-secrets
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.example.com"
```

### Best Practices

1. ✅ **Never Commit Secrets** - Use .gitignore
2. ✅ **Separate per Environment** - Different secrets for staging/prod
3. ✅ **Rotate Regularly** - Every 90 days minimum
4. ✅ **Least Privilege** - Minimal permissions
5. ✅ **Encrypt at Rest** - Kubernetes encryption enabled
6. ✅ **Audit Access** - Log who accesses secrets
7. ✅ **Use Secret Managers** - Vault/AWS/Azure for production

### Rotation Schedule

| Secret Type | Frequency | Method |
|-------------|-----------|--------|
| Database passwords | 90 days | Manual/automated |
| API keys | 90 days | Provider rotation |
| TLS certificates | 90 days | cert-manager |
| Service tokens | 30 days | K8s auto-rotation |

### .gitignore Protection

Automatically ignored:
```
*.key
*.pem
*.crt
secrets.yaml
secrets.env
kubeconfig
.env
credentials.json
```

---

## 🧪 Testing Guide

### Test Locally

```bash
# Run application
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Test with Docker
docker build -t python-app:test .
docker run -p 8000:8000 python-app:test
curl http://localhost:8000/health
```

### Test with kind

```bash
# Create cluster
kind create cluster --name test

# Build and load
docker build -t python-app:local .
kind load docker-image python-app:local --name test

# Deploy
kubectl apply -f k8s/ -n default
kubectl set image deployment/python-app python-app=python-app:local

# Test
kubectl port-forward deployment/python-app 8000:8000
curl http://localhost:8000/health
```

### Test Pipeline

**Pull Request:** Only builds and tests
```bash
git checkout -b feature/test
git push origin feature/test
# Create PR - no deployment
```

**Staging:** Auto-deploys
```bash
git checkout develop
git push origin develop
# Watch in Actions tab
```

**Production:** Requires approval
```bash
git checkout main
git merge develop
git push origin main
# Approve in Actions tab
```

---

## 📁 Project Structure

```
.
├── .github/workflows/
│   ├── ci-cd-pipeline.yml    # Main pipeline (6 stages)
│   └── rollback.yml          # Rollback workflow
├── app/
│   ├── __init__.py
│   └── main.py               # FastAPI application
├── tests/
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── k8s/
│   ├── namespace.yaml        # Staging + production
│   ├── deployment.yaml       # Deployment with health checks
│   └── service.yaml          # NodePort service
├── Dockerfile                # Multi-stage build
├── requirements.txt          # FastAPI, uvicorn
├── requirements-dev.txt      # pytest, linting tools
└── README.md                 # This file
```
