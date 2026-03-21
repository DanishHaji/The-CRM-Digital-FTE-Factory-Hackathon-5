#!/usr/bin/env python3
"""
Web Form Load Generator - Digital FTE 24-Hour Test

Generates realistic web form submissions to test system under load.
Target: 100+ submissions over 24 hours with varying patterns.
"""

import asyncio
import random
import time
from datetime import datetime
from typing import List, Dict
import aiohttp
import json
from faker import Faker

# Initialize Faker for realistic data
fake = Faker()


class WebFormLoadGenerator:
    """Generate load for web support form endpoint."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        requests_per_hour: int = 10,
        duration_hours: int = 24,
    ):
        self.api_url = api_url
        self.requests_per_hour = requests_per_hour
        self.duration_hours = duration_hours
        self.results: List[Dict] = []
        self.start_time = None

    def generate_realistic_message(self) -> str:
        """Generate realistic customer support messages."""
        templates = [
            "I need help resetting my password. I've tried the forgot password link but haven't received an email.",
            "How do I update my billing information? I want to change my payment method.",
            "I'm having trouble logging into my account. It says my credentials are invalid.",
            "Can you help me understand how to use feature X? I can't find the documentation.",
            "I want to cancel my subscription. What's the process?",
            "I was charged twice this month. Can you refund one of the charges?",
            "The application is running very slow. Is there a known issue?",
            "How do I export my data? I need it for a report.",
            "I need to upgrade my plan. What are my options?",
            "I'm getting an error message when I try to save my work. Error code: 500",
            "Can someone help me set up integration with service Y?",
            "I forgot my username. Can you help me recover it?",
            "How long does it take for support to respond?",
            "I'm interested in the enterprise plan. Who can I talk to?",
            "The mobile app keeps crashing. Is this a known bug?",
            "I need to add more users to my account. How do I do that?",
            "Can you walk me through the setup process?",
            "I'm seeing unexpected behavior in feature Z. Is this normal?",
            "How do I delete my account permanently?",
            "I need an invoice for my last payment. Can you send it?",
        ]
        return random.choice(templates)

    def generate_submission(self) -> Dict:
        """Generate a realistic web form submission."""
        return {
            "name": fake.name(),
            "email": fake.email(),
            "message": self.generate_realistic_message(),
        }

    async def submit_form(self, session: aiohttp.ClientSession, submission: Dict) -> Dict:
        """Submit a form and track result."""
        start = time.time()
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "submission": submission,
            "success": False,
            "status_code": None,
            "response_time_ms": 0,
            "error": None,
        }

        try:
            async with session.post(
                f"{self.api_url}/api/support",
                json=submission,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                result["status_code"] = response.status
                result["success"] = response.status == 201
                result["response_time_ms"] = int((time.time() - start) * 1000)

                if result["success"]:
                    data = await response.json()
                    result["ticket_id"] = data.get("ticket_id")
                else:
                    result["error"] = await response.text()

        except asyncio.TimeoutError:
            result["error"] = "Timeout after 30s"
            result["response_time_ms"] = 30000
        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = int((time.time() - start) * 1000)

        return result

    async def run_batch(self, batch_size: int):
        """Run a batch of requests."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(batch_size):
                submission = self.generate_submission()
                tasks.append(self.submit_form(session, submission))

            results = await asyncio.gather(*tasks)
            self.results.extend(results)

            # Log batch summary
            success_count = sum(1 for r in results if r["success"])
            avg_response_time = sum(r["response_time_ms"] for r in results) / len(results)

            print(
                f"[{datetime.utcnow().isoformat()}] Batch complete: "
                f"{success_count}/{batch_size} successful, "
                f"avg response time: {avg_response_time:.0f}ms"
            )

    async def run(self):
        """Run load generator for specified duration."""
        self.start_time = datetime.utcnow()
        print(f"Starting web form load generator at {self.start_time.isoformat()}")
        print(f"Target: {self.requests_per_hour} requests/hour for {self.duration_hours} hours")
        print(f"API URL: {self.api_url}")
        print("-" * 80)

        total_requests = self.requests_per_hour * self.duration_hours
        interval_seconds = 3600 / self.requests_per_hour  # Time between requests

        for i in range(total_requests):
            # Submit single request
            batch_size = 1

            # Occasionally send bursts (10% of the time)
            if random.random() < 0.1:
                batch_size = random.randint(2, 5)
                print(f"[BURST] Sending {batch_size} concurrent requests")

            await self.run_batch(batch_size)

            # Wait before next request (with some randomness)
            jitter = random.uniform(0.8, 1.2)
            wait_time = interval_seconds * jitter
            await asyncio.sleep(wait_time)

            # Progress update every hour
            if (i + 1) % self.requests_per_hour == 0:
                hours_completed = (i + 1) / self.requests_per_hour
                self.print_summary(hours_completed)

        print("\n" + "=" * 80)
        print("Load test complete!")
        self.print_summary(self.duration_hours)
        self.save_results()

    def print_summary(self, hours_completed: float):
        """Print summary statistics."""
        if not self.results:
            return

        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful

        response_times = [r["response_time_ms"] for r in self.results]
        avg_response = sum(response_times) / len(response_times)
        p95_response = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_response = sorted(response_times)[int(len(response_times) * 0.99)]

        print(f"\n{'=' * 80}")
        print(f"Summary after {hours_completed:.1f} hours:")
        print(f"{'=' * 80}")
        print(f"Total requests:     {total}")
        print(f"Successful:         {successful} ({successful/total*100:.1f}%)")
        print(f"Failed:             {failed} ({failed/total*100:.1f}%)")
        print(f"Avg response time:  {avg_response:.0f}ms")
        print(f"P95 response time:  {p95_response:.0f}ms")
        print(f"P99 response time:  {p99_response:.0f}ms")
        print(f"{'=' * 80}\n")

    def save_results(self):
        """Save results to JSON file."""
        filename = f"web_load_results_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(
                {
                    "start_time": self.start_time.isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                    "config": {
                        "api_url": self.api_url,
                        "requests_per_hour": self.requests_per_hour,
                        "duration_hours": self.duration_hours,
                    },
                    "results": self.results,
                    "summary": self.get_summary_stats(),
                },
                f,
                indent=2,
            )
        print(f"Results saved to: {filename}")

    def get_summary_stats(self) -> Dict:
        """Get summary statistics."""
        if not self.results:
            return {}

        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        response_times = [r["response_time_ms"] for r in self.results]

        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": total - successful,
            "success_rate": successful / total * 100,
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "p50_response_time_ms": sorted(response_times)[int(len(response_times) * 0.5)],
            "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)],
            "p99_response_time_ms": sorted(response_times)[int(len(response_times) * 0.99)],
            "max_response_time_ms": max(response_times),
        }


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Web Form Load Generator")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--requests-per-hour",
        type=int,
        default=10,
        help="Requests per hour (default: 10)",
    )
    parser.add_argument(
        "--duration-hours",
        type=float,
        default=24.0,
        help="Duration in hours (default: 24)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (10 requests, 1 minute)",
    )

    args = parser.parse_args()

    # Test mode for quick validation
    if args.test_mode:
        print("Running in TEST MODE (10 requests over 1 minute)")
        generator = WebFormLoadGenerator(
            api_url=args.api_url,
            requests_per_hour=600,  # 10 requests per minute
            duration_hours=1 / 60,  # 1 minute
        )
    else:
        generator = WebFormLoadGenerator(
            api_url=args.api_url,
            requests_per_hour=args.requests_per_hour,
            duration_hours=args.duration_hours,
        )

    try:
        await generator.run()
    except KeyboardInterrupt:
        print("\n\nLoad test interrupted by user")
        generator.save_results()


if __name__ == "__main__":
    asyncio.run(main())
