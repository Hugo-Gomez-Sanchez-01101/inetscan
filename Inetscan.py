import argparse
import ipaddress
import subprocess
import threading
import sys
from queue import Queue

max_threads = 30
semaphore = threading.Semaphore(max_threads)

ports = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]
processed_ips = set()
lock = threading.Lock()
output_queue = Queue()

def start_scan(ip, output_file):
    subnet_ranges = get_subnet_ranges(ip)
    alive_ranges = []

    def check_range(subnet):
        print(f"\n[+] Scanning subnet {subnet}")
        if range_exists(subnet):
            print(f"\033[1;32m[+] Subnet {subnet} is alive\033[0m")
            alive_ranges.append(subnet)
        else:
            print(f"[-] Subnet {subnet} is not alive")

    threads = []
    for subnet in subnet_ranges:
        thread = threading.Thread(target=check_range, args=(subnet,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    print("\n[+] Alive ranges:", alive_ranges)
    with open(output_file, "w") as f:
        f.write("\n".join(alive_ranges) + "\n")

def get_subnet_ranges(network_ip):
    network = ipaddress.IPv4Network(network_ip, strict=False)
    return [str(subnet) for subnet in (network.subnets(new_prefix=24) if network.prefixlen < 24 else [network])]

def ping(ip):
    try:
        result = subprocess.run(['fping', '-a', '-q', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def scan_ports(ip, output_file):
    open_ports = []
    for port in ports:
        try:
            result = subprocess.run(['nc', '-z', '-w1', str(ip), str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                open_ports.append(port)
        except Exception:
            pass
    
    if open_ports:
        with lock:
            with open(output_file, "a") as f:
                f.write(f"{ip}: {', '.join(map(str, open_ports))}\n")

def range_exists(network):
    network = ipaddress.IPv4Network(network, strict=False)
    hosts = list(network.hosts())
    ip_groups = {
        "first_5": hosts[:5],
        "from_50": hosts[50:55] if len(hosts) > 50 else [],
        "from_100": hosts[100:105] if len(hosts) > 100 else [],
        "from_150": hosts[150:155] if len(hosts) > 150 else [],
        "from_200": hosts[200:205] if len(hosts) > 200 else [],
        "from_250": hosts[250:255] if len(hosts) > 250 else [],
    }
    
    alive = False
    lock = threading.Lock()

    def check_ip(ip):
        nonlocal alive
        if ping(ip):
            with lock:
                alive = True
                print(f"\033[1;32m[+] Found {ip} is alive \033[0m")

    threads = []
    for range_name, ips in ip_groups.items():
        if ips:
            print(f"\n[+] Scanning range {range_name}")
            for ip in ips:
                thread = threading.Thread(target=check_ip, args=(ip,))
                threads.append(thread)
                thread.start()
    
    for thread in threads:
        thread.join()

    return alive

def network_scan(ip_range, output_file):
    try:
        network = ipaddress.IPv4Network(ip_range, strict=False)
        total_ips = len(list(network.hosts()))
        progress = 0

        def process_ip(ip):
            with semaphore:
                nonlocal progress
                if ping(ip):
                    scan_ports(ip, output_file)
                with lock:
                    progress += 1
                    show_progress(progress, total_ips)

        threads = []
        for ip in network.hosts():
            thread = threading.Thread(target=process_ip, args=(ip,))
            threads.append(thread)
            thread.start()
            if len(threads) >= max_threads:
                for t in threads:
                    t.join()
                threads = []

        for thread in threads:
            thread.join()

        print("\n[+] Scan complete.")
    except ValueError as e:
        print(e)
        print("[!] Invalid IP range.")

def show_progress(progress, total):
    percentage = (progress / total) * 100
    bar = ('#' * int(percentage / 2)).ljust(50)
    sys.stdout.write(f"\r[ {bar} ] {percentage:3.0f}% completed")
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="Network scanner.")
    parser.add_argument("-i", "--ip", required=True, help="Specify the IP range to scan (e.g., 192.168.1.0/24, 10.0.0.0/16)")
    parser.add_argument("-o", "--output", default="scan_results.txt", help="Specify output file for results")
    args = parser.parse_args()

    print(f"[+] Scanning range: {args.ip}")
    start_scan(args.ip, args.output)
    network_scan(args.ip, args.output)

if __name__ == "__main__":
    main()