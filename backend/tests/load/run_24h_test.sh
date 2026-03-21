#!/bin/bash
# ==================================
# 24-Hour Continuous Operation Test
# ==================================
#
# Orchestrates the complete 24-hour stress test:
# - Web form load generation (100+ requests)
# - Metrics collection (uptime, latency)
# - Chaos engineering (pod kills every 2 hours)
#
# Success Criteria:
# - Uptime > 99.9%
# - P95 latency < 3s
# - Zero message loss
# - Proper autoscaling

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
DURATION_HOURS="${DURATION_HOURS:-24}"
TEST_MODE="${TEST_MODE:-false}"

echo "========================================"
echo "24-Hour Continuous Operation Test"
echo "========================================"
echo ""
echo "Configuration:"
echo "  API URL:          $API_URL"
echo "  Duration:         $DURATION_HOURS hours"
echo "  Test mode:        $TEST_MODE"
echo ""
echo "Success Criteria:"
echo "  ✓ Uptime > 99.9%"
echo "  ✓ P95 latency < 3s"
echo "  ✓ Escalation rate < 25%"
echo "  ✓ Zero message loss"
echo ""
echo "========================================"
echo ""

# Check dependencies
echo "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null && [ "$TEST_MODE" != "true" ]; then
    echo -e "${YELLOW}Warning: kubectl not found (required for chaos engineering)${NC}"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q aiohttp faker 2>/dev/null || echo "Dependencies already installed"

# Create results directory
RESULTS_DIR="results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"
cd "$RESULTS_DIR"

echo -e "${GREEN}Results will be saved to: $RESULTS_DIR${NC}"
echo ""

# Start timestamp
START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "Test started at: $START_TIME"
echo ""

# Function to handle cleanup
cleanup() {
    echo ""
    echo "========================================"
    echo "Stopping all background processes..."
    echo "========================================"

    # Kill all background jobs
    jobs -p | xargs -r kill 2>/dev/null

    echo "Cleanup complete"
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Start all test components in parallel
echo "Starting test components..."
echo ""

# 1. Start metrics collector
echo -e "${GREEN}[1/3] Starting metrics collector...${NC}"
if [ "$TEST_MODE" = "true" ]; then
    python3 ../metrics_collector.py \
        --api-url "$API_URL" \
        --duration 0.017 \
        --interval 5 \
        > metrics.log 2>&1 &
else
    python3 ../metrics_collector.py \
        --api-url "$API_URL" \
        --duration "$DURATION_HOURS" \
        --interval 60 \
        > metrics.log 2>&1 &
fi
METRICS_PID=$!
echo "  PID: $METRICS_PID"
echo "  Log: metrics.log"
echo ""

# 2. Start web load generator
echo -e "${GREEN}[2/3] Starting web load generator...${NC}"
if [ "$TEST_MODE" = "true" ]; then
    python3 ../web_load_generator.py \
        --api-url "$API_URL" \
        --test-mode \
        > web_load.log 2>&1 &
else
    python3 ../web_load_generator.py \
        --api-url "$API_URL" \
        --requests-per-hour 10 \
        --duration-hours "$DURATION_HOURS" \
        > web_load.log 2>&1 &
fi
WEB_LOAD_PID=$!
echo "  PID: $WEB_LOAD_PID"
echo "  Log: web_load.log"
echo ""

# 3. Start chaos engineering (if kubectl available)
if command -v kubectl &> /dev/null; then
    echo -e "${GREEN}[3/3] Starting chaos engineering...${NC}"
    if [ "$TEST_MODE" = "true" ]; then
        python3 ../../chaos/pod_killer.py \
            --duration 0.017 \
            --kill-interval 0.008 \
            --test-mode \
            > chaos.log 2>&1 &
    else
        python3 ../../chaos/pod_killer.py \
            --duration "$DURATION_HOURS" \
            --kill-interval 2 \
            > chaos.log 2>&1 &
    fi
    CHAOS_PID=$!
    echo "  PID: $CHAOS_PID"
    echo "  Log: chaos.log"
    echo ""
else
    echo -e "${YELLOW}[3/3] Skipping chaos engineering (kubectl not available)${NC}"
    echo ""
    CHAOS_PID=""
fi

echo "========================================"
echo "All test components started!"
echo "========================================"
echo ""
echo "Monitor progress with:"
echo "  tail -f $RESULTS_DIR/metrics.log"
echo "  tail -f $RESULTS_DIR/web_load.log"
if [ -n "$CHAOS_PID" ]; then
    echo "  tail -f $RESULTS_DIR/chaos.log"
fi
echo ""
echo "Press Ctrl+C to stop the test early"
echo ""
echo "========================================"
echo ""

# Wait for all background processes
echo "Waiting for test completion..."
echo ""

# Function to check if process is still running
is_running() {
    kill -0 "$1" 2>/dev/null
}

# Monitor test progress
while is_running $METRICS_PID || is_running $WEB_LOAD_PID || is_running $CHAOS_PID; do
    sleep 60

    # Print progress
    ELAPSED=$(( $(date +%s) - $(date -d "$START_TIME" +%s) ))
    HOURS=$(( ELAPSED / 3600 ))
    MINS=$(( (ELAPSED % 3600) / 60 ))

    echo "[$(date -u +"%H:%M:%S")] Elapsed: ${HOURS}h ${MINS}m"

    # Check if processes crashed
    if ! is_running $METRICS_PID; then
        echo -e "${YELLOW}Warning: Metrics collector stopped${NC}"
    fi
    if ! is_running $WEB_LOAD_PID; then
        echo -e "${YELLOW}Warning: Web load generator stopped${NC}"
    fi
    if [ -n "$CHAOS_PID" ] && ! is_running $CHAOS_PID; then
        echo -e "${YELLOW}Warning: Chaos engineering stopped${NC}"
    fi
done

# Test complete
echo ""
echo "========================================"
echo "24-Hour Test Complete!"
echo "========================================"
echo ""
echo "End time: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Validate results
echo "Validating results..."
echo ""

if [ -f "metrics_results_"*.json ]; then
    echo -e "${GREEN}✓ Metrics results found${NC}"
else
    echo -e "${RED}✗ Metrics results NOT found${NC}"
fi

if [ -f "web_load_results_"*.json ]; then
    echo -e "${GREEN}✓ Web load results found${NC}"
else
    echo -e "${RED}✗ Web load results NOT found${NC}"
fi

if [ -f "chaos_results_"*.json ]; then
    echo -e "${GREEN}✓ Chaos results found${NC}"
else
    echo -e "${YELLOW}⚠ Chaos results NOT found (may be disabled)${NC}"
fi

echo ""
echo "Results saved in: $RESULTS_DIR"
echo ""
echo "Next steps:"
echo "  1. Review results: cat $RESULTS_DIR/metrics_results_*.json"
echo "  2. Analyze logs: less $RESULTS_DIR/metrics.log"
echo "  3. Validate criteria: python3 ../validate_results.py $RESULTS_DIR"
echo ""
echo "========================================"
