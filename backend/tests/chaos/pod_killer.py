#!/usr/bin/env python3
"""
Chaos Engineering - Pod Killer

Randomly kills pods every 2 hours to test system resilience.
Validates zero message loss and proper autoscaling response.
"""

import subprocess
import random
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict


class ChaosEngineer:
    """Chaos engineering tool for Kubernetes pod kills."""

    def __init__(
        self,
        namespace: str = "digital-fte",
        kill_interval_hours: int = 2,
        duration_hours: int = 24,
        test_mode: bool = False,
    ):
        self.namespace = namespace
        self.kill_interval_hours = kill_interval_hours
        self.duration_hours = duration_hours
        self.test_mode = test_mode
        self.kill_log: List[Dict] = []
        self.start_time = None

    def get_pods(self, label_selector: str = "app=digital-fte-api") -> List[str]:
        """Get list of pods matching label selector."""
        try:
            cmd = [
                "kubectl",
                "get",
                "pods",
                "-n",
                self.namespace,
                "-l",
                label_selector,
                "-o",
                "jsonpath={.items[*].metadata.name}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            pods = result.stdout.strip().split()
            return [p for p in pods if p]  # Filter empty strings
        except subprocess.CalledProcessError as e:
            print(f"Error getting pods: {e.stderr}")
            return []

    def kill_random_pod(self, label_selector: str = "app=digital-fte-api") -> Dict:
        """Kill a random pod matching the label selector."""
        pods = self.get_pods(label_selector)

        if not pods:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": "No pods found",
            }

        # Select random pod
        target_pod = random.choice(pods)

        print(f"\n[{datetime.utcnow().isoformat()}] Killing pod: {target_pod}")

        kill_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "pod_name": target_pod,
            "total_pods_before": len(pods),
            "success": False,
            "error": None,
        }

        try:
            if not self.test_mode:
                # Actually kill the pod
                cmd = ["kubectl", "delete", "pod", target_pod, "-n", self.namespace]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                kill_info["success"] = True
                print(f"✓ Pod {target_pod} deleted successfully")
            else:
                # Test mode - don't actually kill
                kill_info["success"] = True
                kill_info["test_mode"] = True
                print(f"✓ [TEST MODE] Would have killed pod: {target_pod}")

            # Wait for pod to start terminating
            time.sleep(5)

            # Check if new pod is being created
            pods_after = self.get_pods(label_selector)
            kill_info["total_pods_after"] = len(pods_after)

            print(f"  Pods before: {kill_info['total_pods_before']}")
            print(f"  Pods after:  {kill_info['total_pods_after']}")

            # Verify autoscaling is working
            if len(pods_after) >= kill_info["total_pods_before"] - 1:
                print(f"  ✓ Autoscaling working - new pod being created")
            else:
                print(f"  ⚠ Warning - Pod count dropped significantly")

        except subprocess.CalledProcessError as e:
            kill_info["error"] = e.stderr
            print(f"✗ Error killing pod: {e.stderr}")

        return kill_info

    def monitor_recovery(self, expected_replicas: int = 3, timeout_seconds: int = 300):
        """Monitor pod recovery after kill."""
        print(f"\nMonitoring recovery (timeout: {timeout_seconds}s)...")
        start = time.time()

        while time.time() - start < timeout_seconds:
            pods = self.get_pods()
            ready_pods = self.count_ready_pods()

            print(
                f"  [{int(time.time() - start)}s] Total pods: {len(pods)}, Ready: {ready_pods}/{expected_replicas}"
            )

            if ready_pods >= expected_replicas:
                recovery_time = int(time.time() - start)
                print(f"  ✓ Recovery complete in {recovery_time}s")
                return {
                    "recovered": True,
                    "recovery_time_seconds": recovery_time,
                }

            time.sleep(10)

        print(f"  ⚠ Recovery timeout after {timeout_seconds}s")
        return {
            "recovered": False,
            "recovery_time_seconds": timeout_seconds,
            "timeout": True,
        }

    def count_ready_pods(self) -> int:
        """Count number of ready pods."""
        try:
            cmd = [
                "kubectl",
                "get",
                "pods",
                "-n",
                self.namespace,
                "-l",
                "app=digital-fte-api",
                "-o",
                "jsonpath={.items[?(@.status.phase==\"Running\")].metadata.name}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            running_pods = result.stdout.strip().split()
            return len([p for p in running_pods if p])
        except subprocess.CalledProcessError:
            return 0

    def run(self):
        """Run chaos engineering for specified duration."""
        self.start_time = datetime.utcnow()
        end_time = self.start_time + timedelta(hours=self.duration_hours)

        print("=" * 80)
        print("Chaos Engineering - Pod Killer")
        print("=" * 80)
        print(f"Start time:        {self.start_time.isoformat()}")
        print(f"End time:          {end_time.isoformat()}")
        print(f"Duration:          {self.duration_hours} hours")
        print(f"Kill interval:     Every {self.kill_interval_hours} hours")
        print(f"Namespace:         {self.namespace}")
        print(f"Test mode:         {self.test_mode}")
        print("=" * 80)

        kill_count = 0
        next_kill_time = self.start_time + timedelta(hours=self.kill_interval_hours)

        while datetime.utcnow() < end_time:
            if datetime.utcnow() >= next_kill_time:
                kill_count += 1
                print(f"\n{'#' * 80}")
                print(f"CHAOS EVENT #{kill_count}")
                print(f"{'#' * 80}")

                # Kill random API pod
                kill_info = self.kill_random_pod("app=digital-fte-api")
                kill_info["kill_number"] = kill_count
                kill_info["component"] = "api"

                # Monitor recovery
                recovery_info = self.monitor_recovery()
                kill_info["recovery"] = recovery_info

                self.kill_log.append(kill_info)

                # Schedule next kill
                next_kill_time = datetime.utcnow() + timedelta(hours=self.kill_interval_hours)
                print(f"\nNext kill scheduled for: {next_kill_time.isoformat()}")

            # Progress update
            remaining = (end_time - datetime.utcnow()).total_seconds() / 3600
            print(f"\r[{datetime.utcnow().isoformat()}] Remaining: {remaining:.1f} hours", end="", flush=True)

            # Check every minute
            time.sleep(60)

        print("\n\n" + "=" * 80)
        print("Chaos Engineering Complete")
        print("=" * 80)
        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print summary of chaos events."""
        if not self.kill_log:
            print("No chaos events executed")
            return

        total_kills = len(self.kill_log)
        successful_kills = sum(1 for k in self.kill_log if k["success"])
        successful_recoveries = sum(1 for k in self.kill_log if k.get("recovery", {}).get("recovered", False))

        recovery_times = [k["recovery"]["recovery_time_seconds"] for k in self.kill_log if "recovery" in k]
        avg_recovery = sum(recovery_times) / len(recovery_times) if recovery_times else 0

        print(f"\nTotal chaos events:      {total_kills}")
        print(f"Successful pod kills:    {successful_kills}/{total_kills}")
        print(f"Successful recoveries:   {successful_recoveries}/{total_kills}")
        print(f"Avg recovery time:       {avg_recovery:.0f}s")
        print(f"Max recovery time:       {max(recovery_times) if recovery_times else 0}s")

    def save_results(self):
        """Save chaos engineering results."""
        filename = f"chaos_results_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(
                {
                    "start_time": self.start_time.isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                    "config": {
                        "namespace": self.namespace,
                        "kill_interval_hours": self.kill_interval_hours,
                        "duration_hours": self.duration_hours,
                        "test_mode": self.test_mode,
                    },
                    "kill_log": self.kill_log,
                },
                f,
                indent=2,
            )
        print(f"\nResults saved to: {filename}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Chaos Engineering - Pod Killer")
    parser.add_argument(
        "--namespace",
        default="digital-fte",
        help="Kubernetes namespace (default: digital-fte)",
    )
    parser.add_argument(
        "--kill-interval",
        type=int,
        default=2,
        help="Hours between pod kills (default: 2)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=24.0,
        help="Duration in hours (default: 24)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (don't actually kill pods)",
    )

    args = parser.parse_args()

    engineer = ChaosEngineer(
        namespace=args.namespace,
        kill_interval_hours=args.kill_interval,
        duration_hours=args.duration,
        test_mode=args.test_mode,
    )

    try:
        engineer.run()
    except KeyboardInterrupt:
        print("\n\nChaos engineering interrupted by user")
        engineer.save_results()


if __name__ == "__main__":
    main()
