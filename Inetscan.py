#implementar --top-ports
from tools.network_verifyer import verify_network
from tools.network_scanner import scan_networks
from rich.console import Console
import argparse
import json


console = Console()


def start_scan(ip, output_file, aggressive, timeout):
    
    #Subnet verification
    alive_ranges = verify_network(ip, aggressive, timeout)
    
    console.print("\n[bold yellow]Network/s Verified! Results:[/bold yellow]", alive_ranges)
    with open( f"results/" + output_file + "_alive_ranges.txt", "w") as f:
        f.write("\n".join(alive_ranges) + "\n")

    #Port scan
    ports = scan_networks(alive_ranges)

    console.print("\n[bold yellow]All Ports Scaned! Scan Finished[/bold yellow]")
    with open(f"results/" + output_file + "_ports_scan.txt", "w") as f:
        json.dump(ports, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Network scanner.")
    parser.add_argument("-i", "--ip", required=True, help="Specify the IP range to scan (e.g., 192.168.1.0/24, 10.0.0.0/16)")
    parser.add_argument("-o", "--output", default="results", help="Specify output file for results")
    parser.add_argument("-a", "--aggressive", action='store_true', help="Enable aggressive mode (multi-threaded subnetwork scanning)")
    parser.add_argument("-t", "--timeout", type=int, help="Set timeout for fping in milliseconds (default: system-defined)")
    args = parser.parse_args()

    timeout_msg = f"{args.timeout} ms" if args.timeout is not None else "default system timeout"
    console.print(f"[bold cyan][+] Scanning range: {args.ip} with timeout {timeout_msg}[/bold cyan]")
    
    start_scan(args.ip, args.output, args.aggressive, args.timeout)


if __name__ == "__main__":
    main()