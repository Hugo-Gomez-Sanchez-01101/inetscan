import argparse
import ipaddress
import subprocess
import threading
import time
from queue import Queue
from rich.console import Console
from rich.table import Table

console = Console()

max_threads = 30
semaphore = threading.Semaphore(max_threads)

ports = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]
processed_ips = set()
lock = threading.Lock()
output_queue = Queue()

def start_scan(ip, output_file, aggressive, timeout):
    alive_ranges = verify_ranges()
    scan_networks(alive_ranges)
    

def main():
    parser = argparse.ArgumentParser(description="Network scanner.")
    parser.add_argument("-i", "--ip", required=True, help="Specify the IP range to scan (e.g., 192.168.1.0/24, 10.0.0.0/16)")
    parser.add_argument("-o", "--output", default="scan_results.txt", help="Specify output file for results")
    parser.add_argument("-a", "--aggressive", action='store_true', help="Enable aggressive mode (multi-threaded range scanning)")
    parser.add_argument("-t", "--timeout", type=int, help="Set timeout for fping in milliseconds (default: system-defined)")
    args = parser.parse_args()

    timeout_msg = f"{args.timeout} ms" if args.timeout is not None else "default system timeout"
    console.print(f"[bold cyan][+] Scanning range: {args.ip} with timeout {timeout_msg}[/bold cyan]")
    
    start_scan(args.ip, args.output, args.aggressive, args.timeout)


if __name__ == "__main__":
    main()