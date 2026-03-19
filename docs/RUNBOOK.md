# Runbook - Digital FTE Customer Success Agent

Incident response procedures and troubleshooting guide for production operations.

## Table of Contents

1. [Emergency Contacts](#emergency-contacts)
2. [Quick Reference](#quick-reference)
3. [Incident Response Procedures](#incident-response-procedures)
4. [Common Issues](#common-issues)
5. [Performance Degradation](#performance-degradation)
6. [Data Issues](#data-issues)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Disaster Recovery](#disaster-recovery)

## Emergency Contacts

### On-Call Rotation
- **Primary**: [Your Name] - [Phone] - [Email]
- **Secondary**: [Backup Name] - [Phone] - [Email]
- **Manager**: [Manager Name] - [Phone] - [Email]

### External Services
- **Groq Support**: https://console.groq.com/support (FREE tier - community support)
- **Twilio Support**: https://www.twilio.com/support (24/7 for paid accounts)
- **Google Cloud Support**: https://cloud.google.com/support
- **Kubernetes Cluster**: [Your cluster provider support]

## Quick Reference

### Essential Commands

```bash
# Set namespace context
kubectl config set-context --current --namespace=digital-fte

# Check overall system health
kubectl get pods
kubectl get hpa
kubectl top pods

# View recent logs
kubectl logs -l app=digital-fte-api --tail=100 -f

# Check database connectivity
kubectl run psql-test --image=postgres:16 --rm -it -- \
  psql -h postgres -U digitalfte -d digitalfte_db -c "SELECT 1;"

# Emergency rollback
kubectl rollout undo deployment/digital-fte-api
```

### Key Metrics to Monitor

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| API Pod CPU | < 70% | 70-85% | > 85% |
| API Pod Memory | < 80% | 80-90% | > 90% |
| Database CPU | < 60% | 60-80% | > 80% |
| Database Connections | < 80 | 80-95 | > 95 |
| P95 Response Time | < 3s | 3-5s | > 5s |
| Error Rate | < 1% | 1-5% | > 5% |
| Active Pods | >= 3 | 2 | < 2 |

### Service Status Page

Check these URLs for service health:
- **API Health**: `https://api.yourdomain.com/health`
- **Groq Status**: https://status.groq.com
- **Twilio Status**: https://status.twilio.com
- **Google Cloud Status**: https://status.cloud.google.com

## Incident Response Procedures

### Incident Severity Levels

**SEV1 - Critical**
- Total service outage (all channels down)
- Data loss or corruption
- Security breach
- Response Time: Immediate (< 5 minutes)

**SEV2 - High**
- Partial service outage (1-2 channels down)
- Significant performance degradation (P95 > 10s)
- High error rate (> 10%)
- Response Time: < 30 minutes

**SEV3 - Medium**
- Minor performance issues
- Non-critical feature broken
- Elevated error rate (5-10%)
- Response Time: < 2 hours

**SEV4 - Low**
- Cosmetic issues
- Non-urgent improvements
- Response Time: Next business day

### Incident Response Workflow

1. **Acknowledge**: Acknowledge the alert within SLA
2. **Assess**: Determine severity level
3. **Notify**: Alert on-call team if SEV1/SEV2
4. **Investigate**: Use troubleshooting procedures below
5. **Mitigate**: Apply immediate fixes or rollback
6. **Verify**: Confirm issue resolved
7. **Document**: Update incident log with RCA
8. **Follow-up**: Create post-mortem for SEV1/SEV2

## Common Issues

### 1. All API Pods CrashLooping

**Symptoms**:
- API pods in CrashLoopBackOff state
- Health check endpoint unreachable
- No responses to webhook requests

**Diagnosis**:

```bash
# Check pod status
kubectl get pods -l app=digital-fte-api

# View crash logs
kubectl logs <crashing-pod-name> --previous

# Common crash causes in logs:
# - "connection refused" → Database unreachable
# - "Invalid API key" → Missing/wrong Groq API key
# - "Out of memory" → Memory limit too low
```

**Resolution**:

```bash
# 1. Check database connectivity
kubectl run psql-test --image=postgres:16 --rm -it -- \
  psql -h postgres -U digitalfte -d digitalfte_db

# If database is down, check postgres pods:
kubectl get pods -l app=postgres
kubectl logs <postgres-pod-name>

# 2. Verify secrets exist
kubectl get secret groq-credentials -o yaml
kubectl get secret postgres-credentials -o yaml

# 3. If secrets are missing/invalid, recreate:
kubectl delete secret groq-credentials
kubectl create secret generic groq-credentials \
  --from-literal=api-key=<VALID_GROQ_API_KEY>

# 4. Restart deployment
kubectl rollout restart deployment/digital-fte-api

# 5. If still failing, check resource limits
kubectl describe pod <crashing-pod-name> | grep -A 10 "Limits:"
# Consider increasing memory limits if OOMKilled
```

**Prevention**:
- Monitor pod health continuously
- Set up alerts for CrashLoopBackOff
- Regularly test secret rotation procedures

---

### 2. Groq API Rate Limit Exceeded

**Symptoms**:
- 429 errors in logs: "Rate limit exceeded"
- Customer messages not getting responses
- High latency for successful requests

**Diagnosis**:

```bash
# Check logs for rate limit errors
kubectl logs -l app=digital-fte-api | grep "rate_limit\|429"

# Count rate limit errors in last hour
kubectl logs -l app=digital-fte-api --since=1h | grep -c "429"

# Check Groq dashboard for usage
# Visit: https://console.groq.com
```

**Resolution**:

**Immediate (SEV2)**:

```bash
# 1. Scale down temporarily to reduce request rate
kubectl scale deployment digital-fte-api --replicas=1

# 2. Implement request queuing (if not already done)
# Edit deployment to add RATE_LIMIT_REQUESTS env var
kubectl set env deployment/digital-fte-api RATE_LIMIT_REQUESTS=5

# 3. Monitor until rate limit resets (usually hourly)
```

**Long-term**:
- Upgrade to Groq paid plan for higher limits
- Implement exponential backoff and retry logic
- Add request caching for duplicate questions
- Consider hybrid approach: Groq + fallback to OpenAI

**Prevention**:
- Monitor Groq API usage daily
- Set up alerts at 80% of rate limit
- Implement request queuing from day 1

---

### 3. Database Connection Pool Exhausted

**Symptoms**:
- Errors: "too many connections"
- API pods healthy but requests timing out
- Slow query performance

**Diagnosis**:

```bash
# Check active database connections
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db \
  -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Check max connections limit
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db \
  -c "SHOW max_connections;"

# Identify long-running queries
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db \
  -c "SELECT pid, state, query_start, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"
```

**Resolution**:

```bash
# 1. Kill long-running queries (if safe)
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db \
  -c "SELECT pg_terminate_backend(<pid>);"

# 2. Increase max_connections (temporary)
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db \
  -c "ALTER SYSTEM SET max_connections = 200;"
kubectl rollout restart deployment/postgres

# 3. Implement connection pooling (PgBouncer)
# See deployment guide for PgBouncer setup

# 4. Optimize queries creating locks
# Identify slow queries and add indexes
```

**Prevention**:
- Implement PgBouncer from start
- Set appropriate connection pool sizes per pod
- Monitor connection count continuously
- Regular VACUUM and ANALYZE

---

### 4. WhatsApp Webhook Signature Validation Failing

**Symptoms**:
- 403 Forbidden errors for WhatsApp webhooks
- Logs show "Invalid Twilio signature"
- WhatsApp messages not processed

**Diagnosis**:

```bash
# Check logs for signature validation errors
kubectl logs -l app=digital-fte-api | grep "signature" | tail -20

# Verify Twilio auth token is correct
kubectl get secret twilio-credentials -o jsonpath='{.data.auth-token}' | base64 -d
# Compare with Twilio console: https://console.twilio.com
```

**Resolution**:

```bash
# 1. Verify webhook URL in Twilio console
# Must match exactly: https://api.yourdomain.com/api/webhooks/whatsapp

# 2. Update Twilio auth token if incorrect
kubectl delete secret twilio-credentials
kubectl create secret generic twilio-credentials \
  --from-literal=account-sid=<SID> \
  --from-literal=auth-token=<CORRECT_TOKEN> \
  --from-literal=whatsapp-number=<NUMBER>

# 3. Restart API pods to pick up new secret
kubectl rollout restart deployment/digital-fte-api

# 4. Test with Twilio webhook debugger
# Visit: https://console.twilio.com/us1/develop/sms/logs
```

**Prevention**:
- Document exact webhook URL format
- Test signature validation in staging first
- Set up monitoring for 403 errors on webhook endpoint

---

### 5. High Memory Usage (OOMKilled)

**Symptoms**:
- Pods restarting with OOMKilled status
- "Out of memory" errors in logs
- Requests failing intermittently

**Diagnosis**:

```bash
# Check pod memory usage
kubectl top pods -l app=digital-fte-api

# Check OOMKilled events
kubectl get events --sort-by='.lastTimestamp' | grep OOMKilled

# View pod resource limits
kubectl describe pod <pod-name> | grep -A 5 "Limits:"
```

**Resolution**:

**Immediate**:

```bash
# 1. Increase memory limits
kubectl set resources deployment digital-fte-api \
  --limits=memory=2Gi \
  --requests=memory=1Gi

# 2. Scale out (more pods, less memory each)
kubectl scale deployment digital-fte-api --replicas=6
```

**Investigate**:

```bash
# Check for memory leaks in application
# - Review agent prompt sizes (reduce if > 1000 tokens)
# - Check conversation history loading (limit to last N messages)
# - Monitor embedding cache size
```

**Prevention**:
- Start with generous memory limits (2Gi) and optimize down
- Implement conversation history pagination
- Clear old data from memory periodically
- Set up memory usage alerts

---

### 6. Gmail Pub/Sub Webhook Not Receiving Messages

**Symptoms**:
- Emails to support address not triggering agent
- No entries in logs for Gmail webhooks
- Gmail Pub/Sub topic shows unacked messages

**Diagnosis**:

```bash
# Check if webhook endpoint is reachable
curl -X POST https://api.yourdomain.com/api/webhooks/gmail \
  -H "Content-Type: application/json" \
  -d '{"message": {"data": "test"}}'

# Check Google Cloud Pub/Sub metrics
# Visit: https://console.cloud.google.com/cloudpubsub
# Look for: delivery errors, ack/nack rates

# Verify subscription configuration
gcloud pubsub subscriptions describe gmail-notifications-sub
```

**Resolution**:

```bash
# 1. Verify push endpoint URL is correct
gcloud pubsub subscriptions update gmail-notifications-sub \
  --push-endpoint=https://api.yourdomain.com/api/webhooks/gmail

# 2. Check SSL certificate is valid
curl -vI https://api.yourdomain.com/health

# 3. Verify service account permissions
# Pub/Sub service account needs permission to invoke webhook

# 4. Test with manual publish
gcloud pubsub topics publish gmail-notifications \
  --message='{"emailAddress":"test@example.com"}'

# Check logs for receipt
kubectl logs -l app=digital-fte-api | grep gmail
```

**Prevention**:
- Monitor Pub/Sub delivery success rate
- Set up alerts for unacked messages > 10
- Test Gmail integration in staging regularly

---

### 7. Cross-Channel Customer Linking Failures

**Symptoms**:
- Same customer creating multiple records
- Customer ID accuracy < 95%
- Logs show "No matching customer found"

**Diagnosis**:

```bash
# Query database for duplicate customers
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db -c "
  SELECT email, COUNT(*)
  FROM customers
  GROUP BY email
  HAVING COUNT(*) > 1;
"

# Check customer_identifiers table for orphaned records
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db -c "
  SELECT customer_id, COUNT(*)
  FROM customer_identifiers
  GROUP BY customer_id
  HAVING COUNT(*) > 3;
"

# Check fuzzy matching logic in logs
kubectl logs -l app=digital-fte-api | grep "fuzzy_match"
```

**Resolution**:

```bash
# 1. Merge duplicate customer records (manual SQL)
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db

# Run merge script:
BEGIN;
UPDATE conversations SET customer_id = '<keep-id>' WHERE customer_id = '<duplicate-id>';
UPDATE customer_identifiers SET customer_id = '<keep-id>' WHERE customer_id = '<duplicate-id>';
DELETE FROM customers WHERE customer_id = '<duplicate-id>';
COMMIT;

# 2. Review and adjust fuzzy matching threshold
# Edit: backend/src/utils/fuzzy_matcher.py
# Lower threshold = more aggressive matching (risk of false positives)
# Higher threshold = more conservative (risk of duplicates)

# 3. Ensure phone normalization is consistent
# Test: backend/tests/unit/test_customer_linking.py
```

**Prevention**:
- Monitor customer duplication rate weekly
- Set up alerts for linking accuracy < 95%
- Add manual review workflow for low-confidence matches

---

## Performance Degradation

### Slow Response Times (P95 > 5s)

**Investigation Steps**:

```bash
# 1. Check pod resource usage
kubectl top pods -l app=digital-fte-api

# 2. Check database query performance
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db -c "
  SELECT query, mean_exec_time, calls
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"

# 3. Check Groq API latency
kubectl logs -l app=digital-fte-api | grep "groq_latency" | tail -50

# 4. Check for network issues
kubectl exec -it <api-pod-name> -- ping google.com
kubectl exec -it <api-pod-name> -- curl -w "%{time_total}" https://api.groq.com
```

**Optimization Actions**:

1. **Database**:
   ```sql
   -- Add indexes for frequent queries
   CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
   CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
   CREATE INDEX idx_customer_identifiers_value ON customer_identifiers(identifier_value);

   -- Run VACUUM ANALYZE
   VACUUM ANALYZE;
   ```

2. **Application**:
   - Reduce agent prompt size (< 1000 tokens)
   - Limit conversation history to last 10 messages
   - Implement caching for knowledge base searches

3. **Scaling**:
   ```bash
   # Scale out API pods
   kubectl scale deployment digital-fte-api --replicas=10

   # Verify load distribution
   kubectl get hpa digital-fte-api-hpa
   ```

---

## Data Issues

### Data Corruption or Loss

**Symptoms**:
- Missing customer records
- Incomplete conversation history
- Database integrity errors

**Immediate Actions**:

1. **Stop writes** (if data is actively corrupting):
   ```bash
   kubectl scale deployment digital-fte-api --replicas=0
   ```

2. **Assess damage**:
   ```bash
   kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db

   -- Count records
   SELECT COUNT(*) FROM customers;
   SELECT COUNT(*) FROM conversations;
   SELECT COUNT(*) FROM messages;

   -- Check for orphaned records
   SELECT COUNT(*) FROM conversations
   WHERE customer_id NOT IN (SELECT customer_id FROM customers);
   ```

3. **Restore from backup** (see Disaster Recovery section)

**Prevention**:
- Daily automated backups (see Maintenance Procedures)
- Point-in-time recovery enabled
- Regular backup restoration tests

---

## Maintenance Procedures

### Database Backup

**Automated Daily Backup**:

```bash
# Create CronJob for daily backups
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: digital-fte
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres -U digitalfte digitalfte_db | \
              gzip > /backup/backup-\$(date +%Y%m%d-%H%M%S).sql.gz
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
EOF
```

**Manual Backup**:

```bash
# Create backup immediately
kubectl run postgres-backup --image=postgres:16 --rm -it -- \
  pg_dump -h postgres -U digitalfte digitalfte_db > backup-$(date +%Y%m%d).sql

# Copy backup locally
kubectl cp postgres-backup:/backup/backup-<date>.sql ./backup-<date>.sql
```

### Database Maintenance

**Weekly Maintenance** (Sunday 2 AM):

```bash
# Connect to database
kubectl exec -it <postgres-pod-name> -- psql -U digitalfte -d digitalfte_db

-- Run VACUUM ANALYZE
VACUUM ANALYZE;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Remove unused indexes if idx_scan = 0
```

### Certificate Renewal

Certificates are auto-renewed by cert-manager, but verify:

```bash
# Check certificate expiry
kubectl get certificate -n digital-fte

# Force renewal if needed
kubectl delete certificate digital-fte-tls -n digital-fte
kubectl apply -f k8s/ingress.yaml
```

### Log Rotation

```bash
# Logs are automatically rotated by Kubernetes
# But you can archive old logs manually:

# Export last 7 days of logs
kubectl logs -l app=digital-fte-api --since=168h > logs-$(date +%Y%m%d).txt

# Upload to long-term storage (S3, GCS, etc.)
aws s3 cp logs-$(date +%Y%m%d).txt s3://your-bucket/logs/
```

---

## Disaster Recovery

### Full System Recovery

**Scenario**: Complete cluster failure, need to rebuild from scratch.

**Recovery Steps**:

1. **Provision new cluster** (see docs/DEPLOYMENT.md)

2. **Restore database from backup**:
   ```bash
   # Copy backup to new cluster
   kubectl cp backup-YYYYMMDD.sql <postgres-pod-name>:/tmp/

   # Restore database
   kubectl exec -it <postgres-pod-name> -- \
     psql -U digitalfte -d digitalfte_db < /tmp/backup-YYYYMMDD.sql
   ```

3. **Recreate secrets**:
   ```bash
   kubectl create secret generic groq-credentials --from-literal=api-key=<KEY>
   kubectl create secret generic postgres-credentials --from-literal=password=<PASS>
   kubectl create secret generic twilio-credentials --from-literal=auth-token=<TOKEN>
   ```

4. **Deploy application**:
   ```bash
   kubectl apply -f k8s/api-deployment.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

5. **Verify functionality**:
   ```bash
   # Health check
   curl https://api.yourdomain.com/health

   # Test web form
   curl -X POST https://api.yourdomain.com/api/support -d '{"name":"Test","email":"test@example.com","message":"Test message"}'
   ```

6. **Update webhook URLs** in Gmail/Twilio consoles

**RTO (Recovery Time Objective)**: 2 hours
**RPO (Recovery Point Objective)**: 24 hours (daily backups)

---

## Post-Incident Review Template

After SEV1/SEV2 incidents, complete this template:

```markdown
# Post-Incident Review: [Incident Title]

**Date**: YYYY-MM-DD
**Severity**: SEV1/SEV2/SEV3
**Duration**: HH:MM (start → resolution)
**On-Call**: [Name]

## Summary
[One paragraph describing what happened]

## Timeline
- **HH:MM** - Incident detected (how: alert, user report, etc.)
- **HH:MM** - Investigation started
- **HH:MM** - Root cause identified
- **HH:MM** - Mitigation applied
- **HH:MM** - Incident resolved

## Root Cause
[Technical explanation of what caused the issue]

## Impact
- **Users affected**: [number/percentage]
- **Channels affected**: Web / Gmail / WhatsApp
- **Duration**: HH:MM
- **Messages lost**: [number, if any]

## Resolution
[What was done to fix the issue]

## Follow-Up Actions
1. [ ] [Action item with owner and due date]
2. [ ] [Action item with owner and due date]

## Lessons Learned
- **What went well**:
- **What could be improved**:
- **Prevention measures**:
```

---

## Additional Resources

- **Deployment Guide**: docs/DEPLOYMENT.md
- **Testing Guide**: docs/TESTING.md
- **API Documentation**: docs/API.md
- **Groq API Docs**: https://console.groq.com/docs
- **Twilio Docs**: https://www.twilio.com/docs
- **Kubernetes Docs**: https://kubernetes.io/docs

**Questions?** Contact the on-call engineer or escalate to management.
