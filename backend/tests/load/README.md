# 24-Hour Continuous Operation Test

Complete load testing and chaos engineering suite for the Digital FTE Customer Success Agent.

## Overview

The 24-hour test validates that the Digital FTE can operate continuously under load with:
- **Realistic traffic patterns** (100+ requests over 24 hours)
- **Chaos engineering** (random pod kills every 2 hours)
- **Continuous monitoring** (uptime, latency, error rates)

## Success Criteria

| Metric | Target | Critical? |
|--------|--------|-----------|
| **Uptime** | > 99.9% | ✅ Yes |
| **P95 Latency** | < 3 seconds | ✅ Yes |
| **Message Loss** | < 1% | ✅ Yes |
| **Load Handling** | 100+ requests | ✅ Yes |
| **Chaos Recovery** | 100% recovery | ⚠️ Optional |

## Quick Start

### Prerequisites

1. **System running** (API accessible at http://localhost:8000 or custom URL)
2. **Python 3.11+** with pip
3. **kubectl** (optional, for chaos engineering)

### Install Dependencies

```bash
cd backend/tests/load
pip install aiohttp faker
```

### Run Quick Test (1 minute)

Test the infrastructure before running the full 24-hour test:

```bash
# Test mode: 10 requests over 1 minute
./run_24h_test.sh
export TEST_MODE=true
./run_24h_test.sh
```

### Run Full 24-Hour Test

```bash
# Set API URL (if not localhost)
export API_URL=https://api.yourdomain.com

# Run full test
./run_24h_test.sh
```

## Test Components

### 1. Web Load Generator (`web_load_generator.py`)

Generates realistic web form submissions.

**Features**:
- Realistic customer data (names, emails, messages)
- 20 different message templates
- Occasional burst traffic (10% of requests)
- Response time tracking
- Success/failure logging

**Usage**:

```bash
# Default: 10 requests/hour for 24 hours
python3 web_load_generator.py --api-url http://localhost:8000

# Custom load
python3 web_load_generator.py \
  --api-url https://api.yourdomain.com \
  --requests-per-hour 20 \
  --duration-hours 24

# Test mode (10 requests in 1 minute)
python3 web_load_generator.py --test-mode
```

**Output**:
- `web_load_results_<timestamp>.json` - Complete results with all requests

### 2. Metrics Collector (`metrics_collector.py`)

Continuously monitors system health.

**Metrics Collected**:
- API health status (every 60 seconds)
- Response time (p50, p95, p99)
- Uptime percentage
- Downtime periods
- Pod counts

**Usage**:

```bash
# Default: Sample every 60s for 24 hours
python3 metrics_collector.py --api-url http://localhost:8000

# Custom sampling
python3 metrics_collector.py \
  --api-url https://api.yourdomain.com \
  --interval 30 \
  --duration 24
```

**Output**:
- `metrics_results_<timestamp>.json` - Complete metrics with downtime tracking

### 3. Chaos Engineering (`../chaos/pod_killer.py`)

Randomly kills pods to test resilience.

**Features**:
- Kills random API pod every 2 hours
- Monitors recovery time
- Validates autoscaling
- Tracks pod counts before/after

**Usage**:

```bash
cd ../chaos

# Default: Kill pod every 2 hours for 24 hours
python3 pod_killer.py --namespace digital-fte

# Custom schedule
python3 pod_killer.py \
  --namespace digital-fte \
  --kill-interval 1 \
  --duration 24

# Test mode (don't actually kill pods)
python3 pod_killer.py --test-mode
```

**Output**:
- `chaos_results_<timestamp>.json` - Kill log with recovery times

### 4. Test Orchestrator (`run_24h_test.sh`)

Runs all components in parallel.

**What it does**:
1. Starts metrics collector
2. Starts web load generator
3. Starts chaos engineering (if kubectl available)
4. Monitors all processes
5. Collects results when complete

**Usage**:

```bash
# Default (localhost, 24 hours)
./run_24h_test.sh

# Custom API URL
API_URL=https://api.yourdomain.com ./run_24h_test.sh

# Custom duration
DURATION_HOURS=12 ./run_24h_test.sh

# Test mode (1 minute)
TEST_MODE=true ./run_24h_test.sh
```

**Output**:
- `results_<timestamp>/` directory with all results and logs

### 5. Results Validator (`validate_results.py`)

Validates that all success criteria are met.

**Validations**:
1. ✅ Uptime > 99.9%
2. ✅ P95 latency < 3s
3. ✅ Load generation successful (100+ requests)
4. ⚠️ Chaos recovery (100% recovery rate)
5. ✅ Message loss < 1%

**Usage**:

```bash
# Validate results from a test run
python3 validate_results.py results_20260320_100000

# Example output:
# ✅ UPTIME: 99.95% (PASS)
# ✅ LATENCY: P95 = 1250ms (PASS)
# ✅ LOAD: 240 requests (PASS)
# ✅ CHAOS: 12/12 recoveries (PASS)
# ✅ MESSAGE LOSS: 0.4% (PASS)
#
# 🎉 ALL VALIDATIONS PASSED
```

**Output**:
- `validation_summary.json` - Validation results

## Test Scenarios

### Scenario 1: Local Development Test

Quick validation of the test infrastructure:

```bash
# Start local API
cd backend
uvicorn src.api.main:app --port 8000

# Run 1-minute test (separate terminal)
cd tests/load
TEST_MODE=true ./run_24h_test.sh

# Validate (should complete in ~1 minute)
python3 validate_results.py results_*
```

### Scenario 2: Kubernetes Full Test

Complete 24-hour test on Kubernetes:

```bash
# Set API URL to Ingress
export API_URL=https://api.yourdomain.com

# Run full test
./run_24h_test.sh

# Monitor progress (separate terminal)
tail -f results_*/metrics.log

# After 24 hours, validate
python3 validate_results.py results_*
```

### Scenario 3: High-Load Test

Increased load for stress testing:

```bash
# Run with higher request rate
python3 web_load_generator.py \
  --api-url https://api.yourdomain.com \
  --requests-per-hour 100 \
  --duration-hours 24
```

## Monitoring During Test

### View Real-Time Logs

```bash
# Metrics collector
tail -f results_*/metrics.log

# Web load generator
tail -f results_*/web_load.log

# Chaos engineering
tail -f results_*/chaos.log
```

### Check Test Progress

```bash
# View metrics summary (updates hourly)
grep "Stats after" results_*/metrics.log

# View load summary (updates hourly)
grep "Summary after" results_*/web_load.log

# View chaos events
grep "CHAOS EVENT" results_*/chaos.log
```

### Check Kubernetes Status

```bash
# View pod status
kubectl get pods -n digital-fte

# View HPA status
kubectl get hpa -n digital-fte

# View recent events
kubectl get events -n digital-fte --sort-by='.lastTimestamp' | tail -20
```

## Interpreting Results

### Uptime Calculation

```
Uptime % = (Healthy Samples / Total Samples) × 100
```

- Sample taken every 60 seconds
- 24 hours = 1,440 samples
- 99.9% uptime allows ~1.4 minutes of downtime

### Latency Metrics

- **P50**: 50% of requests faster than this
- **P95**: 95% of requests faster than this (our target)
- **P99**: 99% of requests faster than this

Example:
```
P50: 800ms  - Half of requests under 800ms
P95: 2,500ms - 95% of requests under 2.5s ✅ PASS
P99: 4,200ms - 99% under 4.2s
```

### Message Loss

```
Loss Rate % = ((Total - Successful) / Total) × 100
```

- Acceptable loss: < 1% (due to chaos events)
- Zero loss is ideal but not required

## Troubleshooting

### Test Fails Immediately

**Problem**: Scripts exit with errors

**Solutions**:
1. Check API is running: `curl http://localhost:8000/health`
2. Install dependencies: `pip install aiohttp faker`
3. Check permissions: `chmod +x run_24h_test.sh`

### High Failure Rate

**Problem**: > 5% of requests failing

**Possible Causes**:
- API not scaled properly (check HPA)
- Database connection issues
- Groq API rate limits
- Network issues

**Debug**:
```bash
# Check API logs
kubectl logs -l app=digital-fte-api -n digital-fte --tail=100

# Check pod resource usage
kubectl top pods -n digital-fte

# Check HPA status
kubectl get hpa -n digital-fte
```

### Uptime < 99.9%

**Problem**: Too much downtime

**Possible Causes**:
- Pods crashing (check logs)
- Insufficient replicas (check HPA min replicas)
- Database issues
- Chaos events too frequent

**Debug**:
```bash
# Check pod crashes
kubectl get events -n digital-fte | grep "Killing\|OOMKilled\|Error"

# Check replica count
kubectl get pods -l app=digital-fte-api -n digital-fte

# Review downtime periods in results
cat results_*/metrics_results_*.json | jq '.downtime_periods'
```

### P95 Latency > 3s

**Problem**: Responses too slow

**Possible Causes**:
- Groq API slow
- Database queries not optimized
- Insufficient CPU/memory
- Network latency

**Debug**:
```bash
# Check resource usage
kubectl top pods -n digital-fte

# Check Groq API status
curl https://status.groq.com

# Review slow requests in logs
cat results_*/web_load_results_*.json | jq '.results[] | select(.response_time_ms > 3000)'
```

## Advanced Usage

### Custom Load Patterns

Create your own load generator for specific patterns:

```python
import asyncio
from web_load_generator import WebFormLoadGenerator

class CustomLoadGenerator(WebFormLoadGenerator):
    def generate_realistic_message(self):
        # Your custom message templates
        return "Custom message pattern"

# Run custom generator
generator = CustomLoadGenerator(...)
asyncio.run(generator.run())
```

### Distributed Load Testing

Run load generators from multiple machines:

```bash
# Machine 1
python3 web_load_generator.py --api-url https://api.yourdomain.com --requests-per-hour 50

# Machine 2
python3 web_load_generator.py --api-url https://api.yourdomain.com --requests-per-hour 50

# Combined: 100 requests/hour
```

### Extended Testing

Run longer tests for extended validation:

```bash
# 48-hour test
python3 web_load_generator.py --duration-hours 48

# 7-day test
python3 web_load_generator.py --duration-hours 168
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: 24-Hour Stress Test

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  stress-test:
    runs-on: ubuntu-latest
    timeout-minutes: 1500  # 25 hours

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install aiohttp faker

    - name: Run 24-hour test
      env:
        API_URL: ${{ secrets.API_URL }}
      run: |
        cd backend/tests/load
        ./run_24h_test.sh

    - name: Validate results
      run: |
        cd backend/tests/load
        python3 validate_results.py results_*

    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: stress-test-results
        path: backend/tests/load/results_*
```

## FAQ

**Q: Can I stop the test early?**
A: Yes, press Ctrl+C. Results will be saved for completed portion.

**Q: How much does the 24-hour test cost?**
A: With Groq FREE tier: $0. With 240 requests at $0/request = $0 total.

**Q: Can I run without Kubernetes?**
A: Yes! Chaos engineering will be skipped, but other tests will run.

**Q: What if a test fails?**
A: Review the failure in `validate_results.py` output, fix the issue, and re-run.

**Q: Can I test Gmail and WhatsApp?**
A: For MVP, web form testing is sufficient. Gmail/WhatsApp can be tested separately.

## Next Steps

After successful 24-hour test:

1. ✅ Review all results files
2. ✅ Document any issues found
3. ✅ Update docs/RUNBOOK.md with learnings
4. ✅ Deploy to production
5. ✅ Set up continuous monitoring

---

**Questions?** Check docs/RUNBOOK.md for troubleshooting or create an issue.
