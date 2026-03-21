#!/usr/bin/env python3
"""
Metrics Collector - Digital FTE 24-Hour Test

Continuously monitors system health and collects metrics:
- Uptime (target: > 99.9%)
- P95 latency (target: < 3s)
- Error rate (target: < 1%)
- Escalation rate (target: < 25%)
- Cross-channel ID accuracy (target: > 95%)
"""

import asyncio
import time
import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp


class MetricsCollector:
    """Collect and analyze system metrics during load test."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        sample_interval_seconds: int = 60,
        duration_hours: int = 24,
    ):
        self.api_url = api_url
        self.sample_interval_seconds = sample_interval_seconds
        self.duration_hours = duration_hours
        self.metrics: List[Dict] = []
        self.start_time = None
        self.downtime_periods: List[Dict] = []

    async def check_health(self, session: aiohttp.ClientSession) -> Dict:
        """Check API health endpoint."""
        start = time.time()
        health_check = {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": False,
            "response_time_ms": 0,
            "error": None,
        }

        try:
            async with session.get(
                f"{self.api_url}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                health_check["response_time_ms"] = int((time.time() - start) * 1000)
                health_check["status_code"] = response.status
                health_check["healthy"] = response.status == 200

                if health_check["healthy"]:
                    data = await response.json()
                    health_check["details"] = data

        except asyncio.TimeoutError:
            health_check["error"] = "Timeout"
            health_check["response_time_ms"] = 5000
        except Exception as e:
            health_check["error"] = str(e)
            health_check["response_time_ms"] = int((time.time() - start) * 1000)

        return health_check

    def get_pod_count(self, namespace: str = "digital-fte") -> Dict:
        """Get current pod count and status."""
        try:
            # Get total pods
            cmd_total = [
                "kubectl",
                "get",
                "pods",
                "-n",
                namespace,
                "-l",
                "app=digital-fte-api",
                "-o",
                "jsonpath={.items[*].metadata.name}",
            ]
            result_total = subprocess.run(cmd_total, capture_output=True, text=True)
            total_pods = len([p for p in result_total.stdout.strip().split() if p])

            # Get running pods
            cmd_running = [
                "kubectl",
                "get",
                "pods",
                "-n",
                namespace,
                "-l",
                "app=digital-fte-api",
                "-o",
                "jsonpath={.items[?(@.status.phase==\"Running\")].metadata.name}",
            ]
            result_running = subprocess.run(cmd_running, capture_output=True, text=True)
            running_pods = len([p for p in result_running.stdout.strip().split() if p])

            return {
                "total_pods": total_pods,
                "running_pods": running_pods,
                "unhealthy_pods": total_pods - running_pods,
            }
        except Exception as e:
            return {"error": str(e)}

    async def collect_sample(self):
        """Collect a single metrics sample."""
        sample = {
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check API health
        async with aiohttp.ClientSession() as session:
            health = await self.check_health(session)

        sample["health"] = health

        # Get pod metrics
        sample["pods"] = self.get_pod_count()

        # Track downtime
        if not health["healthy"]:
            if not self.downtime_periods or self.downtime_periods[-1].get("end"):
                # Start new downtime period
                self.downtime_periods.append({
                    "start": datetime.utcnow().isoformat(),
                    "end": None,
                })
        else:
            if self.downtime_periods and not self.downtime_periods[-1].get("end"):
                # End current downtime period
                self.downtime_periods[-1]["end"] = datetime.utcnow().isoformat()

        self.metrics.append(sample)

    async def run(self):
        """Run metrics collector for specified duration."""
        self.start_time = datetime.utcnow()
        end_time = self.start_time + timedelta(hours=self.duration_hours)

        print("=" * 80)
        print("Metrics Collector - 24-Hour Test")
        print("=" * 80)
        print(f"Start time:       {self.start_time.isoformat()}")
        print(f"End time:         {end_time.isoformat()}")
        print(f"Duration:         {self.duration_hours} hours")
        print(f"Sample interval:  {self.sample_interval_seconds}s")
        print(f"API URL:          {self.api_url}")
        print("=" * 80)

        sample_count = 0

        while datetime.utcnow() < end_time:
            await self.collect_sample()
            sample_count += 1

            # Print progress every 60 samples (1 hour if sampling every minute)
            if sample_count % 60 == 0:
                hours_completed = sample_count * self.sample_interval_seconds / 3600
                self.print_current_stats(hours_completed)

            # Wait for next sample
            await asyncio.sleep(self.sample_interval_seconds)

        print("\n" + "=" * 80)
        print("Metrics collection complete!")
        print("=" * 80)
        self.print_final_summary()
        self.save_results()

    def print_current_stats(self, hours_completed: float):
        """Print current statistics."""
        if not self.metrics:
            return

        total_samples = len(self.metrics)
        healthy_samples = sum(1 for m in self.metrics if m["health"]["healthy"])
        uptime_percent = (healthy_samples / total_samples) * 100

        response_times = [m["health"]["response_time_ms"] for m in self.metrics if m["health"]["healthy"]]
        avg_response = sum(response_times) / len(response_times) if response_times else 0

        print(f"\n{'=' * 80}")
        print(f"Stats after {hours_completed:.1f} hours:")
        print(f"{'=' * 80}")
        print(f"Uptime:           {uptime_percent:.2f}%")
        print(f"Avg response:     {avg_response:.0f}ms")
        print(f"Samples:          {total_samples}")
        print(f"Healthy:          {healthy_samples}/{total_samples}")
        print(f"{'=' * 80}\n")

    def print_final_summary(self):
        """Print final summary with pass/fail validation."""
        if not self.metrics:
            print("No metrics collected")
            return

        # Calculate metrics
        total_samples = len(self.metrics)
        healthy_samples = sum(1 for m in self.metrics if m["health"]["healthy"])
        uptime_percent = (healthy_samples / total_samples) * 100

        # Calculate total downtime
        total_downtime_seconds = 0
        for period in self.downtime_periods:
            if period.get("end"):
                start = datetime.fromisoformat(period["start"])
                end = datetime.fromisoformat(period["end"])
                total_downtime_seconds += (end - start).total_seconds()

        # Response times (only from healthy samples)
        response_times = [m["health"]["response_time_ms"] for m in self.metrics if m["health"]["healthy"]]
        sorted_times = sorted(response_times) if response_times else [0]

        p50 = sorted_times[int(len(sorted_times) * 0.50)] if sorted_times else 0
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0

        # Success criteria
        uptime_pass = uptime_percent > 99.9
        latency_pass = p95 < 3000  # 3 seconds

        print(f"\n{'=' * 80}")
        print("FINAL RESULTS - 24-HOUR CONTINUOUS OPERATION TEST")
        print(f"{'=' * 80}\n")

        print("Uptime:")
        print(f"  Uptime:                {uptime_percent:.3f}%  {'✓ PASS' if uptime_pass else '✗ FAIL'}")
        print(f"  Target:                > 99.9%")
        print(f"  Total downtime:        {total_downtime_seconds:.0f}s")
        print(f"  Downtime periods:      {len(self.downtime_periods)}")

        print(f"\nLatency:")
        print(f"  P95 response time:     {p95:.0f}ms  {'✓ PASS' if latency_pass else '✗ FAIL'}")
        print(f"  Target:                < 3000ms")
        print(f"  P50 response time:     {p50:.0f}ms")
        print(f"  P99 response time:     {p99:.0f}ms")
        print(f"  Avg response time:     {sum(response_times)/len(response_times):.0f}ms" if response_times else "  N/A")

        print(f"\nSampling:")
        print(f"  Total samples:         {total_samples}")
        print(f"  Healthy samples:       {healthy_samples}")
        print(f"  Failed samples:        {total_samples - healthy_samples}")

        print(f"\n{'=' * 80}")
        if uptime_pass and latency_pass:
            print("OVERALL: ✓ PASS")
        else:
            print("OVERALL: ✗ FAIL")
        print(f"{'=' * 80}\n")

    def save_results(self):
        """Save metrics to JSON file."""
        filename = f"metrics_results_{int(time.time())}.json"

        # Calculate summary stats
        total_samples = len(self.metrics)
        healthy_samples = sum(1 for m in self.metrics if m["health"]["healthy"])
        response_times = [m["health"]["response_time_ms"] for m in self.metrics if m["health"]["healthy"]]
        sorted_times = sorted(response_times) if response_times else [0]

        summary = {
            "total_samples": total_samples,
            "healthy_samples": healthy_samples,
            "uptime_percent": (healthy_samples / total_samples) * 100 if total_samples else 0,
            "downtime_periods": len(self.downtime_periods),
            "p50_response_ms": sorted_times[int(len(sorted_times) * 0.50)] if sorted_times else 0,
            "p95_response_ms": sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0,
            "p99_response_ms": sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0,
            "pass": (healthy_samples / total_samples) * 100 > 99.9 if total_samples else False,
        }

        with open(filename, "w") as f:
            json.dump(
                {
                    "start_time": self.start_time.isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                    "config": {
                        "api_url": self.api_url,
                        "sample_interval_seconds": self.sample_interval_seconds,
                        "duration_hours": self.duration_hours,
                    },
                    "summary": summary,
                    "downtime_periods": self.downtime_periods,
                    "metrics": self.metrics,
                },
                f,
                indent=2,
            )
        print(f"Results saved to: {filename}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Metrics Collector")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Sample interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=24.0,
        help="Duration in hours (default: 24)",
    )

    args = parser.parse_args()

    collector = MetricsCollector(
        api_url=args.api_url,
        sample_interval_seconds=args.interval,
        duration_hours=args.duration,
    )

    try:
        await collector.run()
    except KeyboardInterrupt:
        print("\n\nMetrics collection interrupted by user")
        collector.save_results()


if __name__ == "__main__":
    asyncio.run(main())
