#!/usr/bin/env python
"""
Convenience script to run load tests.
"""
# Standard library imports
import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Run API load tests")
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode without web UI"
    )
    parser.add_argument(
        "-u",
        "--users",
        type=int,
        default=10,
        help="Number of concurrent users (default: 10)",
    )
    parser.add_argument(
        "-r",
        "--spawn-rate",
        type=int,
        default=1,
        help="Rate of users spawned per second (default: 1)",
    )
    parser.add_argument(
        "-t",
        "--run-time",
        default="1m",
        help="Test duration (e.g., 30s, 5m, 1h) (default: 1m)",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:9001",
        help="API host to test against (default: http://localhost:9001)",
    )
    parser.add_argument(
        "--token",
        default="<token>",
        help="Bearer token for authentication (default: <token>)",
    )

    args = parser.parse_args()

    # Get the path to the locustfile
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    locustfile_path = os.path.join(script_dir, "load_testing", "locustfile.py")

    # Pass token as an environment variable
    os.environ["LOCUST_AUTH_TOKEN"] = args.token

    # Ensure scripts directory is in Python path
    if script_dir not in sys.path:
        sys.path.insert(0, project_root)

    # Build the command
    cmd = ["locust", "-f", locustfile_path, "--host", args.host]

    # Add specific user class to avoid issues with abstract base class
    cmd.extend(["--class-picker", "--only-summary"])

    if args.headless:
        cmd.extend(
            [
                "--headless",
                "-u",
                str(args.users),
                "-r",
                str(args.spawn_rate),
                "-t",
                args.run_time,
            ]
        )
        # In headless mode, we need to specify the user class directly
        cmd.extend(["--user-classes", "ChatApiUser"])

    # Run the command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nLoad test interrupted.")


if __name__ == "__main__":
    main()
