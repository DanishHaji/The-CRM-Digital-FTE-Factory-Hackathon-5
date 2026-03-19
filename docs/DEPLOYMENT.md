# Deployment Guide - Digital FTE Customer Success Agent

Complete guide for deploying the Digital FTE to production using Kubernetes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Kubernetes Manifests](#kubernetes-manifests)
4. [Deployment Steps](#deployment-steps)
5. [Verification](#verification)
6. [Scaling](#scaling)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Infrastructure

- **Kubernetes Cluster**: v1.25+ (GKE, EKS, AKS, or Minikube for local)
- **kubectl**: v1.25+ configured with cluster access
- **PostgreSQL 16**: Managed database (Cloud SQL, RDS, Azure Database) or self-hosted
- **Domain Name**: For webhook endpoints (Gmail, WhatsApp)
- **SSL Certificate**: For HTTPS webhooks (Let's Encrypt or cloud provider)

### Required API Accounts

- **Groq API**: FREE tier at https://console.groq.com
- **Google Cloud**: Gmail API enabled (if using Gmail channel)
- **Twilio**: WhatsApp approved number (if using WhatsApp channel)

### kubectl Access

```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes

# Create namespace
kubectl create namespace digital-fte
kubectl config set-context --current --namespace=digital-fte
```

## Environment Configuration

### 1. Create Kubernetes Secrets

```bash
# Database credentials
kubectl create secret generic postgres-credentials \
  --from-literal=username=digitalfte \
  --from-literal=password=<STRONG_PASSWORD> \
  --from-literal=database=digitalfte_db \
  -n digital-fte

# Groq API key (FREE from https://console.groq.com)
kubectl create secret generic groq-credentials \
  --from-literal=api-key=<YOUR_GROQ_API_KEY> \
  -n digital-fte

# Twilio credentials (for WhatsApp)
kubectl create secret generic twilio-credentials \
  --from-literal=account-sid=<TWILIO_ACCOUNT_SID> \
  --from-literal=auth-token=<TWILIO_AUTH_TOKEN> \
  --from-literal=whatsapp-number=<TWILIO_WHATSAPP_NUMBER> \
  -n digital-fte

# Gmail credentials (optional, for Gmail channel)
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=./gmail_credentials.json \
  -n digital-fte
```

### 2. Create ConfigMap

```bash
kubectl create configmap digital-fte-config \
  --from-literal=groq-model=llama-3.3-70b-versatile \
  --from-literal=max-tokens=1000 \
  --from-literal=temperature=0.7 \
  --from-literal=log-level=INFO \
  -n digital-fte
```

## Kubernetes Manifests

### 1. PostgreSQL Deployment (if not using managed database)

**k8s/postgres-deployment.yaml**:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: digital-fte
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: standard  # Or your cloud provider's storage class
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: digital-fte
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: pgvector/pgvector:pg16
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: database
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: digital-fte
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

### 2. FastAPI Backend Deployment

**k8s/api-deployment.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: digital-fte-api
  namespace: digital-fte
spec:
  replicas: 3  # Start with 3 replicas
  selector:
    matchLabels:
      app: digital-fte-api
  template:
    metadata:
      labels:
        app: digital-fte-api
    spec:
      containers:
      - name: api
        image: <YOUR_REGISTRY>/digital-fte-api:latest
        ports:
        - containerPort: 8000
        env:
        # Database
        - name: DATABASE_URL
          value: postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres:5432/$(POSTGRES_DB)
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: database

        # Groq AI
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: groq-credentials
              key: api-key
        - name: GROQ_MODEL
          valueFrom:
            configMapKeyRef:
              name: digital-fte-config
              key: groq-model

        # Twilio WhatsApp
        - name: TWILIO_ACCOUNT_SID
          valueFrom:
            secretKeyRef:
              name: twilio-credentials
              key: account-sid
        - name: TWILIO_AUTH_TOKEN
          valueFrom:
            secretKeyRef:
              name: twilio-credentials
              key: auth-token
        - name: TWILIO_WHATSAPP_NUMBER
          valueFrom:
            secretKeyRef:
              name: twilio-credentials
              key: whatsapp-number

        # Gmail (optional)
        - name: GMAIL_CREDENTIALS_FILE
          value: /etc/gmail/credentials.json

        # App config
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: digital-fte-config
              key: log-level

        volumeMounts:
        - name: gmail-credentials
          mountPath: /etc/gmail
          readOnly: true

        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

      volumes:
      - name: gmail-credentials
        secret:
          secretName: gmail-credentials
          optional: true
---
apiVersion: v1
kind: Service
metadata:
  name: digital-fte-api
  namespace: digital-fte
spec:
  selector:
    app: digital-fte-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer  # Or ClusterIP with Ingress
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: digital-fte-api-hpa
  namespace: digital-fte
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: digital-fte-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 3. Ingress for HTTPS Webhooks

**k8s/ingress.yaml**:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: digital-fte-ingress
  namespace: digital-fte
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: digital-fte-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: digital-fte-api
            port:
              number: 80
```

### 4. Database Migration Job

**k8s/migration-job.yaml**:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: digital-fte
spec:
  template:
    spec:
      containers:
      - name: migration
        image: <YOUR_REGISTRY>/digital-fte-api:latest
        command: ["python", "-m", "src.database.migrations.run"]
        env:
        - name: DATABASE_URL
          value: postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres:5432/$(POSTGRES_DB)
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: database
      restartPolicy: OnFailure
  backoffLimit: 3
```

## Deployment Steps

### 1. Build and Push Docker Image

```bash
# Build backend image
cd backend
docker build -t <YOUR_REGISTRY>/digital-fte-api:latest .
docker push <YOUR_REGISTRY>/digital-fte-api:latest

# Build frontend image (optional, for web form)
cd ../frontend
docker build -t <YOUR_REGISTRY>/digital-fte-web:latest .
docker push <YOUR_REGISTRY>/digital-fte-web:latest
```

### 2. Deploy PostgreSQL

```bash
# Apply PostgreSQL manifests
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

### 3. Run Database Migrations

```bash
# Run migration job
kubectl apply -f k8s/migration-job.yaml

# Check migration status
kubectl logs job/db-migration

# Seed knowledge base (one-time)
kubectl run seed-kb --image=<YOUR_REGISTRY>/digital-fte-api:latest \
  --restart=Never \
  --env="DATABASE_URL=postgresql://..." \
  -- python -m src.database.seed_knowledge_base

# Generate embeddings (one-time)
kubectl run generate-embeddings --image=<YOUR_REGISTRY>/digital-fte-api:latest \
  --restart=Never \
  --env="DATABASE_URL=postgresql://..." \
  --env="GROQ_API_KEY=..." \
  -- python -m src.database.generate_embeddings
```

### 4. Deploy API Service

```bash
# Apply API manifests
kubectl apply -f k8s/api-deployment.yaml

# Wait for API pods to be ready
kubectl wait --for=condition=ready pod -l app=digital-fte-api --timeout=300s

# Check logs
kubectl logs -l app=digital-fte-api --tail=100 -f
```

### 5. Deploy Ingress (for HTTPS webhooks)

```bash
# Install cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Apply Ingress
kubectl apply -f k8s/ingress.yaml

# Get external IP
kubectl get ingress digital-fte-ingress
```

### 6. Configure Webhooks

Once your domain is configured with HTTPS:

**Gmail Webhook** (Google Cloud Console):
- Pub/Sub topic: `gmail-notifications`
- Push endpoint: `https://api.yourdomain.com/api/webhooks/gmail`

**WhatsApp Webhook** (Twilio Console):
- When a message comes in: `https://api.yourdomain.com/api/webhooks/whatsapp`

## Verification

### 1. Health Checks

```bash
# Check pod status
kubectl get pods -n digital-fte

# Check API health endpoint
curl https://api.yourdomain.com/health

# Expected response:
# {"status": "healthy", "database": "connected", "groq": "available"}
```

### 2. Test Web Form

```bash
# Submit test request
curl -X POST https://api.yourdomain.com/api/support \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "This is a test message for the Digital FTE"
  }'

# Check logs
kubectl logs -l app=digital-fte-api --tail=50 | grep "test@example.com"
```

### 3. Test WhatsApp

Send a message to your Twilio WhatsApp number and verify:
1. Webhook receives message
2. Customer record created/linked
3. Agent processes message
4. Response sent back via Twilio

```bash
# Check WhatsApp logs
kubectl logs -l app=digital-fte-api | grep "whatsapp"
```

## Scaling

### Manual Scaling

```bash
# Scale API pods manually
kubectl scale deployment digital-fte-api --replicas=10

# Verify scaling
kubectl get pods -l app=digital-fte-api
```

### Horizontal Pod Autoscaling (HPA)

```bash
# Check HPA status
kubectl get hpa digital-fte-api-hpa

# Watch HPA in action
kubectl get hpa digital-fte-api-hpa --watch

# Generate load to trigger scaling (optional)
kubectl run load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://digital-fte-api/health; done"
```

### Database Scaling

For managed databases (Cloud SQL, RDS, Azure Database):
- **Vertical Scaling**: Increase CPU/memory via cloud console
- **Read Replicas**: Add read replicas for query-heavy workloads
- **Connection Pooling**: Use PgBouncer for connection management

## Monitoring

### 1. Kubernetes Dashboard

```bash
# Install Kubernetes Dashboard (if not available)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Create admin user
kubectl create serviceaccount dashboard-admin -n kubernetes-dashboard
kubectl create clusterrolebinding dashboard-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=kubernetes-dashboard:dashboard-admin

# Get access token
kubectl -n kubernetes-dashboard create token dashboard-admin

# Access dashboard
kubectl proxy
# Visit: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### 2. Prometheus & Grafana (Recommended)

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Visit: http://localhost:3000 (admin/prom-operator)
```

### 3. Application Logs

```bash
# View API logs
kubectl logs -l app=digital-fte-api --tail=100 -f

# View logs for specific pod
kubectl logs <pod-name> -f

# Export logs to file
kubectl logs -l app=digital-fte-api --since=24h > api-logs.txt
```

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Common causes:
# - Missing secrets
# - Insufficient resources
# - Image pull errors

# Fix: Verify secrets exist
kubectl get secrets -n digital-fte

# Fix: Increase node resources or reduce requests
```

#### 2. Database Connection Errors

```bash
# Test database connectivity from pod
kubectl run psql-test --image=postgres:16 --rm -it -- \
  psql -h postgres -U digitalfte -d digitalfte_db

# If connection fails:
# - Verify service: kubectl get svc postgres
# - Check credentials: kubectl get secret postgres-credentials -o yaml
```

#### 3. Webhook 4xx/5xx Errors

```bash
# Check API logs for errors
kubectl logs -l app=digital-fte-api | grep "ERROR"

# Common causes:
# - Missing Groq API key
# - Invalid Twilio signature
# - Database connection issues

# Fix: Verify environment variables
kubectl exec -it <pod-name> -- env | grep GROQ
kubectl exec -it <pod-name> -- env | grep TWILIO
```

#### 4. High Memory Usage

```bash
# Check memory usage
kubectl top pods -l app=digital-fte-api

# If pods are OOMKilled:
# - Increase memory limits in deployment
# - Optimize agent prompts (reduce token usage)
# - Add more replicas to distribute load
```

#### 5. Groq API Rate Limits

```bash
# Check logs for rate limit errors
kubectl logs -l app=digital-fte-api | grep "rate_limit"

# Solutions:
# - Upgrade to Groq paid plan
# - Implement request queuing
# - Add retry logic with exponential backoff
```

### Emergency Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/digital-fte-api

# Verify rollback
kubectl rollout status deployment/digital-fte-api

# Check revision history
kubectl rollout history deployment/digital-fte-api
```

## Security Best Practices

### 1. Secret Management

- **Never commit secrets to Git**
- Use Kubernetes Secrets or external secret managers (HashiCorp Vault, AWS Secrets Manager)
- Rotate credentials regularly

### 2. Network Policies

Create network policies to restrict pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: digital-fte-network-policy
  namespace: digital-fte
spec:
  podSelector:
    matchLabels:
      app: digital-fte-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # For Groq API, Twilio, Gmail
```

### 3. RBAC

Implement least-privilege access control:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: digital-fte-role
  namespace: digital-fte
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: digital-fte-rolebinding
  namespace: digital-fte
subjects:
- kind: ServiceAccount
  name: default
  namespace: digital-fte
roleRef:
  kind: Role
  name: digital-fte-role
  apiGroup: rbac.authorization.k8s.io
```

## Cost Optimization

### 1. Resource Requests

Right-size your resource requests based on actual usage:

```bash
# Monitor actual resource usage
kubectl top pods -l app=digital-fte-api

# Adjust requests/limits accordingly
# Start conservative, increase based on metrics
```

### 2. Groq FREE Tier

- **$0/month** for Groq API (FREE tier)
- Monitor usage at https://console.groq.com
- If FREE tier is exhausted, upgrade to paid plan or implement rate limiting

### 3. Database Optimization

- Use connection pooling (PgBouncer)
- Regular VACUUM and ANALYZE
- Archive old conversations/messages

## Production Checklist

Before going live:

- [ ] SSL certificates configured and valid
- [ ] Secrets created in Kubernetes
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] HPA configured and tested
- [ ] Webhook URLs configured in Gmail/Twilio
- [ ] Health checks passing
- [ ] Load testing completed (see docs/TESTING.md)
- [ ] Incident response procedures documented (see docs/RUNBOOK.md)
- [ ] DNS records configured for your domain
- [ ] Firewall rules configured (if applicable)

## Next Steps

- Review **docs/RUNBOOK.md** for incident response procedures
- Set up monitoring dashboards (Grafana)
- Configure alerts for critical issues
- Plan for 24-hour stress test (Phase 10)

---

**Questions or issues?** Check docs/RUNBOOK.md for common scenarios and troubleshooting steps.
