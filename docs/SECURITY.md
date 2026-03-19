# Security Guide - Digital FTE Customer Success Agent

Comprehensive security hardening, audit procedures, and best practices for production deployment.

## Table of Contents

1. [Security Overview](#security-overview)
2. [Threat Model](#threat-model)
3. [Security Checklist](#security-checklist)
4. [Authentication & Authorization](#authentication--authorization)
5. [Data Protection](#data-protection)
6. [Network Security](#network-security)
7. [Application Security](#application-security)
8. [Infrastructure Security](#infrastructure-security)
9. [Incident Response](#incident-response)
10. [Compliance](#compliance)
11. [Security Audit Procedures](#security-audit-procedures)

## Security Overview

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimum necessary permissions
3. **Zero Trust**: Verify every request, trust nothing by default
4. **Security by Design**: Security built-in, not bolted-on
5. **Fail Secure**: System defaults to secure state on failure

### Attack Surface

**External**:
- Web support form (POST /api/support)
- Gmail webhook (POST /api/webhooks/gmail)
- WhatsApp webhook (POST /api/webhooks/whatsapp)
- Ticket query endpoints (GET /api/tickets/*)

**Internal**:
- Database (PostgreSQL 16)
- Groq AI API (external service)
- Gmail API (if Gmail channel enabled)
- Twilio API (if WhatsApp channel enabled)

## Threat Model

### High-Priority Threats

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| **SQL Injection** | Critical | Medium | Parameterized queries, ORM, input validation |
| **API Key Leakage** | Critical | Medium | Secrets management, .gitignore, rotation |
| **DDoS Attack** | High | High | Rate limiting, CDN, auto-scaling |
| **Webhook Spoofing** | High | Medium | Signature validation (HMAC) |
| **XSS (Web Form)** | High | Low | Input sanitization, CSP headers |
| **Data Breach** | Critical | Low | Encryption at rest/transit, access control |
| **Man-in-the-Middle** | High | Low | HTTPS only, certificate pinning |
| **Credential Stuffing** | Medium | Medium | Rate limiting, CAPTCHA (future) |

### Medium-Priority Threats

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| **Groq API Abuse** | Medium | Medium | Rate limiting, request validation |
| **Email Spam** | Medium | High | Email validation, rate limiting |
| **Log Injection** | Medium | Low | Structured logging, log sanitization |
| **Information Disclosure** | Medium | Low | Error handling, remove debug info |

## Security Checklist

### Pre-Production Deployment

#### Critical (Must Complete)

- [ ] **All secrets stored in Kubernetes Secrets** (not in code/env files)
- [ ] **DEBUG=false** in production
- [ ] **ENABLE_API_DOCS=false** (disable Swagger UI)
- [ ] **HTTPS/TLS enabled** for all endpoints (webhooks require HTTPS)
- [ ] **Database passwords** are strong (32+ characters, randomly generated)
- [ ] **Twilio signature validation enabled** (TWILIO_VALIDATE_SIGNATURE=true)
- [ ] **Rate limiting configured** for all public endpoints
- [ ] **CORS origins** restricted to your domains only
- [ ] **.gitignore includes** .env, .env.production, credentials.json
- [ ] **SQL injection protection** (using parameterized queries)
- [ ] **Input validation** on all endpoints (Pydantic models)
- [ ] **Error messages sanitized** (no stack traces to users)

#### High Priority (Strongly Recommended)

- [ ] **Firewall rules** configured (only allow necessary ports)
- [ ] **Network policies** in Kubernetes (pod-to-pod communication)
- [ ] **RBAC configured** (least privilege access)
- [ ] **Secrets rotation policy** established (quarterly)
- [ ] **Database encryption at rest** enabled
- [ ] **Audit logging** enabled for all data access
- [ ] **Monitoring and alerting** for security events
- [ ] **Incident response plan** documented (see docs/RUNBOOK.md)
- [ ] **Backup encryption** enabled
- [ ] **Container image scanning** (for vulnerabilities)

#### Medium Priority (Recommended)

- [ ] **WAF (Web Application Firewall)** configured
- [ ] **DDoS protection** (CloudFlare, AWS Shield, etc.)
- [ ] **Penetration testing** completed
- [ ] **Security headers** configured (CSP, HSTS, X-Frame-Options)
- [ ] **Dependency scanning** (Snyk, Dependabot)
- [ ] **CAPTCHA** on web form (if spam is an issue)
- [ ] **API versioning** strategy defined
- [ ] **Regular security audits** scheduled (quarterly)

---

## Authentication & Authorization

### Current Implementation

**Public Endpoints** (No Authentication):
- Web support form
- Health checks
- Ticket queries (by email)

**Webhook Endpoints** (Signature Validation):
- **Gmail**: Google Cloud Pub/Sub signature (automatic)
- **WhatsApp**: Twilio HMAC-SHA1 signature validation

### Webhook Signature Validation

#### Twilio WhatsApp Signature

**How it works**:
1. Twilio computes HMAC-SHA1 signature of request
2. Signature sent in `X-Twilio-Signature` header
3. Our API recomputes signature and compares

**Implementation** (backend/src/channels/whatsapp_handler.py:validate_twilio_signature):

```python
def validate_twilio_signature(url: str, params: Dict[str, str], signature: str) -> bool:
    """Validate Twilio webhook signature using HMAC-SHA1."""
    import hmac
    import hashlib
    import base64

    # Build validation string
    data = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))

    # Compute expected signature
    expected_signature = base64.b64encode(
        hmac.new(
            settings.twilio_auth_token.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)
```

**Security Best Practices**:
- ✅ Uses constant-time comparison (`hmac.compare_digest`)
- ✅ Auth token stored in Kubernetes Secret
- ✅ Signature validation enabled by default
- ⚠️ Disable ONLY for local testing (SKIP_SIGNATURE_VALIDATION=true)

#### Gmail Pub/Sub Signature

**How it works**:
- Google Cloud Pub/Sub automatically validates subscriptions
- Push endpoint must respond with 200 OK to acknowledge
- Invalid endpoints are automatically disabled

**Security Best Practices**:
- ✅ Use HTTPS endpoint (required by Pub/Sub)
- ✅ Restrict service account permissions
- ✅ Monitor for unexpected Pub/Sub failures

---

### Future: API Key Authentication (Optional)

For future internal API access:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

---

## Data Protection

### Encryption at Rest

#### Database Encryption

**PostgreSQL 16 with pgvector**:

1. **Managed Cloud Databases** (Recommended):
   - **Google Cloud SQL**: Automatic encryption at rest (AES-256)
   - **AWS RDS**: Enable encryption when creating instance
   - **Azure Database**: Encryption enabled by default

2. **Self-Hosted PostgreSQL**:
   ```bash
   # Enable transparent data encryption (TDE)
   # Requires PostgreSQL built with --with-ssl

   # Create encrypted tablespace
   CREATE TABLESPACE encrypted_ts
     LOCATION '/var/lib/postgresql/data/encrypted'
     WITH (encryption = true);

   # Use encrypted tablespace for sensitive tables
   CREATE TABLE customers (
     ...
   ) TABLESPACE encrypted_ts;
   ```

#### Backup Encryption

```bash
# Encrypt backups with GPG
pg_dump digitalfte_db | gzip | gpg -e -r admin@yourdomain.com > backup.sql.gz.gpg

# Decrypt backup
gpg -d backup.sql.gz.gpg | gunzip | psql digitalfte_db
```

---

### Encryption in Transit

#### HTTPS/TLS for All Endpoints

**Certificate Management with cert-manager**:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: digital-fte-tls
  namespace: digital-fte
spec:
  secretName: digital-fte-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.yourdomain.com
  privateKey:
    algorithm: RSA
    size: 2048
```

**Minimum TLS Version**: TLS 1.2
**Recommended**: TLS 1.3

**Nginx Ingress Configuration**:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: digital-fte-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: digital-fte-tls
```

---

### Sensitive Data Handling

#### PII (Personally Identifiable Information)

**Data We Collect**:
- Customer name
- Email address
- Phone number (WhatsApp)
- Support messages
- Conversation history

**Data Protection Measures**:

1. **Storage**:
   - Email stored as lowercase (normalized)
   - Phone numbers normalized to E.164 format
   - Messages stored in encrypted database

2. **Access Control**:
   - No public API to list all customers
   - Ticket queries require customer email
   - Audit logging for all data access

3. **Retention**:
   - Define retention policy (e.g., 2 years)
   - Implement auto-deletion of old data
   - Provide customer data export/deletion on request (GDPR)

4. **Logging**:
   - ⚠️ **Never log PII in plain text**
   - Mask email addresses in logs: `j***@example.com`
   - Mask phone numbers: `+1***8886`

**Example: Safe Logging**:

```python
def mask_email(email: str) -> str:
    """Mask email for logging: john@example.com → j***@example.com"""
    if not email or '@' not in email:
        return "***"
    local, domain = email.split('@', 1)
    return f"{local[0]}***@{domain}"

def mask_phone(phone: str) -> str:
    """Mask phone for logging: +14155238886 → +1***8886"""
    if len(phone) < 8:
        return "***"
    return f"{phone[:3]}***{phone[-4:]}"

# Usage
logger.info("customer_request", email=mask_email(email), phone=mask_phone(phone))
```

---

## Network Security

### Kubernetes Network Policies

Restrict pod-to-pod communication:

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

  # Ingress rules
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000

  # Egress rules
  egress:
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53

  # Allow PostgreSQL
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432

  # Allow HTTPS (for Groq, Twilio, Gmail APIs)
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

---

### Firewall Rules

**Cloud Provider Firewall**:

```bash
# Google Cloud (gcloud)
gcloud compute firewall-rules create digital-fte-allow-https \
  --allow tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags digital-fte-api

gcloud compute firewall-rules create digital-fte-allow-health \
  --allow tcp:8000 \
  --source-ranges <load-balancer-ip-range> \
  --target-tags digital-fte-api

# AWS (Security Groups)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Azure (Network Security Groups)
az network nsg rule create \
  --resource-group digital-fte \
  --nsg-name digital-fte-nsg \
  --name AllowHTTPS \
  --protocol tcp --port 443 --priority 100
```

**Only Allow Required Ports**:
- 443 (HTTPS) - Public internet
- 8000 (API) - Load balancer only
- 5432 (PostgreSQL) - API pods only

---

## Application Security

### Input Validation

**Pydantic Models** (automatic validation):

```python
from pydantic import BaseModel, EmailStr, Field, validator

class WebFormSubmission(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr  # Automatic email validation
    message: str = Field(..., min_length=10, max_length=5000)

    @validator('name')
    def validate_name(cls, v):
        # Strip whitespace
        v = v.strip()
        # Reject if empty after stripping
        if len(v) < 2:
            raise ValueError("Name too short")
        # Reject suspicious patterns
        if '<script' in v.lower() or 'javascript:' in v.lower():
            raise ValueError("Invalid name format")
        return v
```

**SQL Injection Prevention**:

✅ **Good** (Parameterized queries):
```python
# Using asyncpg (parameterized)
row = await conn.fetchrow(
    "SELECT * FROM customers WHERE email = $1",
    email  # Automatically escaped
)
```

❌ **Bad** (String concatenation):
```python
# NEVER DO THIS!
query = f"SELECT * FROM customers WHERE email = '{email}'"
row = await conn.fetchrow(query)
```

---

### XSS (Cross-Site Scripting) Prevention

**Content Security Policy (CSP) Headers**:

```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.groq.com; "
            "frame-ancestors 'none';"
        )

        # Other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

# Add to FastAPI app
app.add_middleware(SecurityHeadersMiddleware)
```

---

### Rate Limiting

**Implementation with slowapi**:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/support")
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def handle_web_submission(request: Request, submission: WebFormSubmission):
    ...
```

**Rate Limit Recommendations**:
- Web form: 100 requests/minute per IP
- Ticket queries: 1000 requests/hour per email
- Health checks: Unlimited (for monitoring)

---

### Error Handling

**Sanitize Error Messages**:

✅ **Good** (Generic error):
```python
try:
    result = await process_request()
except Exception as exc:
    logger.error("request_failed", error=str(exc), exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Failed to process request. Please try again."
    )
```

❌ **Bad** (Exposes internals):
```python
try:
    result = await process_request()
except Exception as exc:
    raise HTTPException(
        status_code=500,
        detail=f"Database error: {exc}"  # Exposes database structure!
    )
```

---

## Infrastructure Security

### Container Security

#### Image Scanning

```bash
# Scan Docker image for vulnerabilities
docker scan <image-name>

# Using Trivy (recommended)
trivy image <image-name>

# Fail build if HIGH or CRITICAL vulnerabilities found
trivy image --severity HIGH,CRITICAL --exit-code 1 <image-name>
```

#### Dockerfile Best Practices

```dockerfile
# Use specific version tags (not "latest")
FROM python:3.11.8-slim

# Run as non-root user
RUN useradd -m -u 1000 digitalfte
USER digitalfte

# Don't include secrets in image
# Use Kubernetes Secrets instead

# Minimize attack surface (slim base image)
# Only install required dependencies

# Set read-only filesystem
# (Configure in Kubernetes pod spec)
```

---

### Kubernetes Security

#### Pod Security Policy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: digital-fte-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  readOnlyRootFilesystem: true
  volumes:
  - 'configMap'
  - 'secret'
  - 'emptyDir'
```

#### RBAC (Role-Based Access Control)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: digital-fte-role
  namespace: digital-fte
rules:
# Read-only access to pods and services
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]

# No access to secrets (managed separately)
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: digital-fte-rolebinding
  namespace: digital-fte
subjects:
- kind: ServiceAccount
  name: digital-fte-sa
  namespace: digital-fte
roleRef:
  kind: Role
  name: digital-fte-role
  apiGroup: rbac.authorization.k8s.io
```

---

### Secrets Management

#### Kubernetes Secrets

✅ **Good** (Kubernetes Secrets):
```bash
kubectl create secret generic groq-credentials \
  --from-literal=api-key=$GROQ_API_KEY \
  --namespace=digital-fte

# Reference in deployment
env:
- name: GROQ_API_KEY
  valueFrom:
    secretKeyRef:
      name: groq-credentials
      key: api-key
```

❌ **Bad** (Environment variables in deployment):
```yaml
# NEVER DO THIS!
env:
- name: GROQ_API_KEY
  value: "gsk_hardcoded_api_key_here"  # Visible in Git!
```

#### External Secrets (Advanced)

**Using Google Secret Manager**:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: digital-fte-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: digital-fte-secrets
    creationPolicy: Owner
  data:
  - secretKey: groq-api-key
    remoteRef:
      key: groq-api-key
  - secretKey: twilio-auth-token
    remoteRef:
      key: twilio-auth-token
```

---

## Incident Response

### Security Event Detection

**Monitor for**:
- Failed webhook signature validations
- Repeated 403/401 errors from same IP
- Unusual traffic patterns (DDoS)
- SQL injection attempts in logs
- Database connection failures
- Groq API rate limit errors
- Unexpected data access patterns

### Incident Response Plan

**SEV1 - Security Breach**:

1. **Immediate Actions** (< 5 minutes):
   - Stop data exfiltration (block IP, isolate pod)
   - Notify security team and management
   - Preserve evidence (logs, database snapshots)

2. **Investigation** (< 1 hour):
   - Determine breach scope (what data was accessed)
   - Identify attack vector
   - Assess damage

3. **Containment** (< 2 hours):
   - Patch vulnerability
   - Rotate all secrets (API keys, passwords)
   - Update firewall rules
   - Deploy patched version

4. **Recovery** (< 24 hours):
   - Restore from clean backup if needed
   - Verify system integrity
   - Monitor for re-infection

5. **Post-Incident** (< 7 days):
   - Complete post-mortem
   - Notify affected customers (if PII compromised)
   - Implement additional security controls
   - Update incident response procedures

---

## Compliance

### GDPR (General Data Protection Regulation)

**Data Subject Rights**:

1. **Right to Access**: Customer can request their data
   ```sql
   -- Export all customer data
   SELECT * FROM customers WHERE email = 'customer@example.com';
   SELECT * FROM conversations WHERE customer_id = '...';
   SELECT * FROM messages WHERE conversation_id IN (...);
   ```

2. **Right to Erasure** ("Right to be Forgotten"):
   ```sql
   -- Delete all customer data
   BEGIN;
   DELETE FROM messages WHERE conversation_id IN (
     SELECT conversation_id FROM conversations WHERE customer_id = '...'
   );
   DELETE FROM conversations WHERE customer_id = '...';
   DELETE FROM customer_identifiers WHERE customer_id = '...';
   DELETE FROM customers WHERE customer_id = '...';
   COMMIT;
   ```

3. **Right to Portability**: Provide data in machine-readable format (JSON)

4. **Data Minimization**: Only collect necessary data

**GDPR Compliance Checklist**:
- [ ] Privacy policy published
- [ ] Data retention policy defined
- [ ] Customer data export functionality
- [ ] Customer data deletion functionality
- [ ] Consent management (for marketing emails)
- [ ] Data processing agreement with cloud providers
- [ ] Breach notification procedure (< 72 hours)

---

### HIPAA (If Handling Health Information)

**Note**: Current implementation does NOT handle health information. If you plan to add health-related support:

- [ ] Encrypt all PHI (Protected Health Information)
- [ ] Implement audit logging for all PHI access
- [ ] Sign Business Associate Agreement (BAA) with cloud provider
- [ ] Conduct annual risk assessment
- [ ] Implement access controls (authentication required)

---

## Security Audit Procedures

### Monthly Security Checklist

- [ ] Review access logs for anomalies
- [ ] Check for failed authentication attempts
- [ ] Verify all secrets are still valid (not expired)
- [ ] Review and update firewall rules
- [ ] Check for vulnerable dependencies (npm audit, pip-audit)
- [ ] Verify backups are encrypted and restorable
- [ ] Review Kubernetes RBAC permissions

### Quarterly Security Audit

- [ ] Full penetration testing (external vendor)
- [ ] Code security review
- [ ] Dependency vulnerability scan
- [ ] Review and update incident response plan
- [ ] Rotate all secrets (API keys, passwords, certificates)
- [ ] Review and update security policies
- [ ] Security training for team

### Annual Security Assessment

- [ ] Third-party security audit
- [ ] Compliance audit (GDPR, SOC 2, etc.)
- [ ] Disaster recovery test
- [ ] Review and update threat model
- [ ] Architecture security review

---

### Security Testing Commands

#### 1. Dependency Scanning

```bash
# Python dependencies
pip install pip-audit
pip-audit

# Node.js dependencies (frontend)
cd frontend
npm audit
npm audit fix

# Using Snyk
snyk test
```

#### 2. Container Image Scanning

```bash
# Trivy
trivy image digitalfte-api:latest

# Docker Scout
docker scout cves digitalfte-api:latest
```

#### 3. SAST (Static Application Security Testing)

```bash
# Bandit (Python security linter)
pip install bandit
bandit -r backend/src/

# Semgrep (multi-language)
pip install semgrep
semgrep --config=auto backend/src/
```

#### 4. Secrets Scanning

```bash
# Detect secrets in code
pip install detect-secrets
detect-secrets scan --all-files

# TruffleHog (Git history)
trufflehog filesystem . --json
```

#### 5. API Security Testing

```bash
# OWASP ZAP (automated security scan)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://api.yourdomain.com

# Test for common vulnerabilities
curl -X POST https://api.yourdomain.com/api/support \
  -H "Content-Type: application/json" \
  -d '{"name":"<script>alert(1)</script>","email":"test@example.com","message":"Test XSS"}'
```

---

## Security Contact

**Security Issues**: security@yourdomain.com
**Bug Bounty Program**: (if available)
**Responsible Disclosure**: Report security vulnerabilities privately

---

## Additional Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CIS Kubernetes Benchmark**: https://www.cisecurity.org/benchmark/kubernetes
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **Cloud Security Alliance**: https://cloudsecurityalliance.org/

---

**Last Updated**: 2026-03-20
**Security Policy Version**: 1.0
**Next Review Date**: 2026-06-20
