import argparse
import ipaddress
import subprocess
import threading
import sys
from queue import Queue

max_threads = 80
ports = [21, 22, 23, 25, 79, 80, 88, 135, 3389, 443, 445, 873, 2049, 2375, 2376, 8080, 8081]
processed_ips = set()
lock = threading.Lock()
output_queue = Queue()

def ping_host(ip):
    try:
        result = subprocess.run(['fping', '-a', '-q', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            with lock:
                if ip not in processed_ips:
                    processed_ips.add(ip)
                    output_queue.put(f"\033[1;32m[+] {ip} is alive\033[0m")
                    return True
    except Exception:
        pass
    return False

def scan_ports(ip, ports_file):
    for port in ports:
        try:
            result = subprocess.run(['nc', '-z', '-w1', str(ip), str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                with lock:
                    output_queue.put(f"\033[1;32m[+] {ip}:{port} is open\033[0m")
                    ports_file.write(f"{ip}:{port}\n")
        except Exception:
            pass

def show_progress(progress, total):
    percentage = (progress / total) * 100
    bar = ('#' * int(percentage / 2)).ljust(50)
    sys.stdout.write(f"\r[ {bar} ] {percentage:3.0f}% completed")
    sys.stdout.flush()

def process_output():
    while True:
        message = output_queue.get()
        if message is None:  # Signal to end
            break
        sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line
        print(message, end="\n")
        sys.stdout.flush()

def validate_ranges(ip_range):
    try:
        network = ipaddress.IPv4Network(ip_range, strict=False)
        valid_ranges = []

        def validate_subnet(subnet):
            for host in list(subnet.hosts())[:5]:  # First 5 host IPs
                print(host)
                if ping_host(host):
                    valid_ranges.append(subnet)
                    break

        threads = []
        for subnet in network.subnets(new_prefix=24):  # Subnets of the original range
            while len(threads) >= max_threads:
                for t in threads:
                    if not t.is_alive():
                        threads.remove(t)
            thread = threading.Thread(target=validate_subnet, args=(subnet,))
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()

        return valid_ranges

    except ValueError:
        print("\033[1;31m[!] Invalid IP range.\033[0m")
        return []

def scan_network(valid_ranges, ips_file, ports_file):
    total_ips = sum(len(list(r.hosts())) for r in valid_ranges)
    progress = 0

    def process_ip(ip):
        nonlocal progress
        if ping_host(ip):
            with open(ips_file.name, "a") as f:
                f.write(f"{ip}\n")
            scan_ports(ip, ports_file)
        with lock:
            progress += 1
            show_progress(progress, total_ips)

    threads = []
    for ip_range in valid_ranges:
        for ip in ip_range.hosts():
            while len(threads) >= max_threads:
                for t in threads:
                    if not t.is_alive():
                        threads.remove(t)
            thread = threading.Thread(target=process_ip, args=(ip,))
            threads.append(thread)
            thread.start()

    for t in threads:
        t.join()

    output_queue.put(None)  # Signal to end output thread
    print("\n\033[1;33m[!] \033[1mScan complete.\033[0m")

def main():
    parser = argparse.ArgumentParser(description="Network scanner.")
    parser.add_argument("-i", "--ip", required=True, help="Specify the IP range to scan (e.g., 192.168.1.0/24, 10.0.0.0/8)")
    parser.add_argument("-o", "--output", default="result", help="Base name for the output file (default: 'result')")
    args = parser.parse_args()

    with open(f"{args.output}_alive_ips.txt", "w") as ips_file, open(f"{args.output}_open_ports.txt", "w") as ports_file:
        print(f"\033[1;33m[!] \033[0m\033[1;33mValidating ranges in: {args.ip}\033[0m")

        output_thread = threading.Thread(target=process_output, daemon=True)
        output_thread.start()

        valid_ranges = validate_ranges(args.ip)

        if not valid_ranges:
            print("\033[1;31m[!] No valid ranges found.\033[0m")
            output_queue.put(None)
            return

        print(f"\033[1;33m[!] \033[0m\033[1;33m{len(valid_ranges)} valid ranges found. Starting scan...\033[0m")
        scan_network(valid_ranges, ips_file, ports_file)

        output_thread.join()

