# Kubernetes Deployment for Digital FTE

Complete Kubernetes manifests for deploying the Digital FTE Customer Success Agent to production.

## Prerequisites

1. **Kubernetes Cluster** (v1.25+)
   - Google GKE, AWS EKS, Azure AKS, or local Minikube
   - kubectl configured with cluster access

2. **cert-manager** (for automatic SSL/TLS certificates)
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

3. **Nginx Ingress Controller**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
   ```

4. **Docker Images Built and Pushed**
   ```bash
   # Build and push backend
   cd backend
   docker build -t your-registry/digital-fte-api:latest .
   docker push your-registry/digital-fte-api:latest

   # Build and push frontend (optional)
   cd ../frontend
   docker build -t your-registry/digital-fte-web:latest .
   docker push your-registry/digital-fte-web:latest
   ```

## Deployment Steps

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create Secrets

**Option A: Create secrets from command line (recommended)**

```bash
# Groq API credentials
kubectl create secret generic groq-credentials \
  --from-literal=api-key=YOUR_GROQ_API_KEY \
  -n digital-fte

# PostgreSQL credentials
kubectl create secret generic postgres-credentials \
  --from-literal=username=digitalfte \
  --from-literal=password=$(openssl rand -base64 32) \
  --from-literal=database=digitalfte_db \
  -n digital-fte

# Twilio credentials
kubectl create secret generic twilio-credentials \
  --from-literal=account-sid=YOUR_TWILIO_ACCOUNT_SID \
  --from-literal=auth-token=YOUR_TWILIO_AUTH_TOKEN \
  --from-literal=whatsapp-number=+15558675310 \
  -n digital-fte

# Gmail credentials (optional, for Gmail channel)
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=./path/to/gmail_credentials.json \
  -n digital-fte
```

**Option B: Use secrets.yaml.example**

```bash
# Copy template and fill in values
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with actual values
nano secrets.yaml

# Apply secrets
kubectl apply -f secrets.yaml

# Delete local file (don't commit to Git!)
rm secrets.yaml
```

### 3. Create ConfigMap

```bash
kubectl apply -f configmap.yaml
```

### 4. Create RBAC (ServiceAccount and Role)

```bash
kubectl apply -f rbac.yaml
```

### 5. Deploy PostgreSQL

```bash
kubectl apply -f postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n digital-fte --timeout=300s
```

### 6. Run Database Migrations

```bash
# Create a job to run migrations
kubectl run db-migration \
  --image=your-registry/digital-fte-api:latest \
  --restart=Never \
  --namespace=digital-fte \
  --env="DATABASE_URL=postgresql://digitalfte:PASSWORD@postgres:5432/digitalfte_db" \
  -- python -m src.database.migrations.run

# Check migration logs
kubectl logs db-migration -n digital-fte

# Delete job after completion
kubectl delete pod db-migration -n digital-fte
```

### 7. Seed Knowledge Base (one-time)

```bash
# Seed knowledge base
kubectl run seed-kb \
  --image=your-registry/digital-fte-api:latest \
  --restart=Never \
  --namespace=digital-fte \
  --env="DATABASE_URL=postgresql://digitalfte:PASSWORD@postgres:5432/digitalfte_db" \
  -- python -m src.database.seed_knowledge_base

# Generate embeddings
kubectl run generate-embeddings \
  --image=your-registry/digital-fte-api:latest \
  --restart=Never \
  --namespace=digital-fte \
  --env="DATABASE_URL=postgresql://digitalfte:PASSWORD@postgres:5432/digitalfte_db" \
  --env="GROQ_API_KEY=YOUR_GROQ_API_KEY" \
  -- python -m src.database.generate_embeddings

# Clean up
kubectl delete pod seed-kb generate-embeddings -n digital-fte
```

### 8. Deploy API Service

```bash
# Update image in api-deployment.yaml with your registry
kubectl apply -f api-deployment.yaml

# Wait for API pods to be ready
kubectl wait --for=condition=ready pod -l app=digital-fte-api -n digital-fte --timeout=300s

# Check API logs
kubectl logs -l app=digital-fte-api -n digital-fte --tail=50 -f
```

### 9. Deploy HorizontalPodAutoscaler

```bash
kubectl apply -f api-hpa.yaml

# Check HPA status
kubectl get hpa -n digital-fte
```

### 10. Configure SSL/TLS with cert-manager

```bash
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
```

### 11. Deploy Ingress

```bash
# Update domain in ingress.yaml (api.yourdomain.com → your actual domain)
kubectl apply -f ingress.yaml

# Check Ingress status
kubectl get ingress -n digital-fte

# Get external IP
kubectl get svc -n ingress-nginx
```

### 12. Configure DNS

Point your domain to the Ingress external IP:

```
api.yourdomain.com  A  <EXTERNAL_IP>
```

### 13. Verify Deployment

```bash
# Check all pods
kubectl get pods -n digital-fte

# Check services
kubectl get svc -n digital-fte

# Check certificate
kubectl get certificate -n digital-fte

# Test health endpoint
curl https://api.yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-20T10:30:00Z",
  "database": "connected",
  "ai_provider": "groq (llama-3.3-70b-versatile)"
}
```

### 14. Configure Webhooks

**Gmail Pub/Sub**:
```bash
gcloud pubsub subscriptions update gmail-notifications-sub \
  --push-endpoint=https://api.yourdomain.com/api/webhooks/gmail
```

**Twilio WhatsApp**:
- Go to Twilio Console: https://console.twilio.com
- Configure webhook URL: `https://api.yourdomain.com/api/webhooks/whatsapp`
- HTTP Method: POST

## Monitoring

### View Logs

```bash
# API logs
kubectl logs -l app=digital-fte-api -n digital-fte --tail=100 -f

# PostgreSQL logs
kubectl logs -l app=postgres -n digital-fte --tail=100 -f

# All pods
kubectl logs -l app=digital-fte-api -n digital-fte --all-containers=true
```

### Check Resource Usage

```bash
# Pod resource usage
kubectl top pods -n digital-fte

# Node resource usage
kubectl top nodes

# HPA status
kubectl get hpa -n digital-fte --watch
```

### Check Events

```bash
kubectl get events -n digital-fte --sort-by='.lastTimestamp'
```

## Scaling

### Manual Scaling

```bash
# Scale API pods
kubectl scale deployment digital-fte-api --replicas=10 -n digital-fte

# Verify scaling
kubectl get pods -l app=digital-fte-api -n digital-fte
```

### Autoscaling (HPA)

HPA is already configured and will automatically scale based on CPU/memory:
- Min replicas: 3
- Max replicas: 20
- Target CPU: 70%
- Target Memory: 80%

## Updates

### Rolling Update

```bash
# Build and push new image
docker build -t your-registry/digital-fte-api:v1.1.0 .
docker push your-registry/digital-fte-api:v1.1.0

# Update deployment
kubectl set image deployment/digital-fte-api \
  api=your-registry/digital-fte-api:v1.1.0 \
  -n digital-fte

# Watch rollout
kubectl rollout status deployment/digital-fte-api -n digital-fte

# Rollback if needed
kubectl rollout undo deployment/digital-fte-api -n digital-fte
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n digital-fte

# Check logs
kubectl logs <pod-name> -n digital-fte

# Common issues:
# - Missing secrets
# - Image pull errors
# - Insufficient resources
```

### Database Connection Errors

```bash
# Test database connectivity
kubectl run psql-test --image=postgres:16 --rm -it -n digital-fte -- \
  psql -h postgres -U digitalfte -d digitalfte_db

# If connection fails:
# - Verify service: kubectl get svc postgres -n digital-fte
# - Check credentials: kubectl get secret postgres-credentials -o yaml -n digital-fte
```

### Certificate Issues

```bash
# Check certificate status
kubectl describe certificate digital-fte-tls -n digital-fte

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager
```

## Clean Up

```bash
# Delete all resources
kubectl delete namespace digital-fte

# Or delete individual resources
kubectl delete -f ingress.yaml
kubectl delete -f api-hpa.yaml
kubectl delete -f api-deployment.yaml
kubectl delete -f postgres.yaml
kubectl delete -f configmap.yaml
kubectl delete -f rbac.yaml
kubectl delete -f namespace.yaml
```

## Production Checklist

Before deploying to production:

- [ ] Secrets created securely (not from YAML files)
- [ ] SSL/TLS certificate issued and valid
- [ ] DNS configured correctly
- [ ] Database backups configured
- [ ] Monitoring and alerting set up (Prometheus, Grafana)
- [ ] Resource limits configured (prevent resource exhaustion)
- [ ] HPA tested (scale up and down)
- [ ] Logging configured (ELK, Loki, CloudWatch)
- [ ] Security scanning completed (Trivy, Snyk)
- [ ] Load testing completed
- [ ] Disaster recovery plan documented

## Additional Resources

- **Deployment Guide**: `../docs/DEPLOYMENT.md`
- **Runbook**: `../docs/RUNBOOK.md`
- **Security Guide**: `../docs/SECURITY.md`
- **API Documentation**: `../docs/API.md`

---

**Questions?** Check the docs or create an issue in the repository.
