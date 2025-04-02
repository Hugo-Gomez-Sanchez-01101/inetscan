from tools.network_verifyer import Network_Verifyer
from tools.network_scanner import Network_Scanner
from rich.console import Console
import argparse
import json
import sys

console = Console()
error_console = Console(stderr=True)

COMMON_PORTS = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]

def start_scan(ip, ports, output_file, aggressive, timeout, max_threads):
    # Subnet verification
    network_verifyer = Network_Verifyer(max_threads)
    alive_ranges = network_verifyer.verify_network(ip, aggressive, timeout)
    
    console.print("\n[bold yellow]Network/s Verified! Results:[/bold yellow]", alive_ranges)
    with open(f"results/{output_file}_alive_ranges.txt", "w") as f:
        f.write("\n".join(alive_ranges) + "\n")

    # Port scan
    if ports:
        network_scaner = Network_Scanner(max_threads)
        scan_results = network_scanner.scan_networks(alive_ranges, ports)

        console.print("\n[bold yellow]All Ports Scanned! Scan Finished[/bold yellow]")
        with open(f"results/{output_file}_ports_scan.txt", "w") as f:
            json.dump(scan_results, f, indent=4)


def get_ports(limite):
    try:
        with open("top_ports.txt", "r") as f:
            contenido = f.read()
        puertos = contenido.split(',')
        return puertos[:limite]
    except FileNotFoundError:
        error_console.print("[bold red]Error: top_ports.txt not found.[/bold red]")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Network scanner.")
    parser.add_argument("-i", "--ip", required=True, help="Specify the IP range to scan (e.g., 192.168.1.0/24, 10.0.0.0/16)")
    parser.add_argument("-o", "--output", default="results", help="Specify output file for results")
    parser.add_argument("-a", "--aggressive", action='store_true', help="Enable aggressive mode (multi-threaded subnetwork scanning)")
    parser.add_argument("-ti", "--timeout", type=int, help="Set timeout for fping in milliseconds (default: system-defined)")
    parser.add_argument("-m", "--max-threads", type=int, default=30, help="Set the number of threads (default: 30 threads)")
    parser.add_argument("-p", "--port", type=int, help="Port to scan")
    parser.add_argument("--top-ports", type=int, help="Most common ports to scan")
    parser.add_argument("--common-ports", action="store_true", help="Scan a predefined list of common ports")
    args = parser.parse_args()

    selected_options = sum(opt is not None for opt in [args.port, args.top_ports]) + args.common_ports
    if selected_options > 1:
        console.print("[bold red]Error: You can only use one of -p, --top-ports, or --common-ports.[/bold red]")
        sys.exit(1)

    if args.common_ports:
        ports = COMMON_PORTS
    elif args.top_ports:
        if args.top_ports > 1000 or args.top_ports < 1:
            error_console.print("[bold red]Error: you can only select a range of top ports from 1>= to <=1000")
        ports = get_ports(args.top_ports)
    elif args.port:
        ports = [args.port]
    else:
        ports = []

    timeout_msg = f"{args.timeout} ms" if args.timeout is not None else "default system timeout"
    console.print(f"[bold cyan][+] Scanning network: {args.ip} with timeout {timeout_msg}[/bold cyan]")
    
    start_scan(args.ip, ports, args.output, args.aggressive, args.timeout, args.max_threads)

if __name__ == "__main__":
    main()
