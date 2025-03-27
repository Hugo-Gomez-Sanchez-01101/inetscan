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


def start_scan(ip, aggressive):
    subnet_ranges = get_subnet_ranges(ip)
    alive_ranges = []

    def scan_subnet(subnet_range):
        with semaphore:
            if range_exists(subnet_range):
                if aggressive:
                    network_scan(subnet_range)
                else:
                    alive_ranges.append(subnet_range)

    threads = []
    for subnet_range in subnet_ranges:
        thread = threading.Thread(target=scan_subnet, args=(subnet_range,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if not aggressive:
        threads = []
        for subnet_range in alive_ranges:
            thread = threading.Thread(target=network_scan, args=(subnet_range,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


def get_subnet_ranges(network_ip):
    network = ipaddress.IPv4Network(network_ip, strict=False)
    return [str(subnet) for subnet in (network.subnets(new_prefix=24) if network.prefixlen < 24 else [network])]


def ping(ip):
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
                    output_queue.put(f"\033[1;32m[+] {ip}:{port} open \033[0m")
                    ports_file.write(f"{ip}:{port}\n")
        except Exception:
            pass


def range_exists(network):
    hosts = list(network.hosts())
    ip_groups = {
        "first_5": hosts[:5],
        "from_50": hosts[50:55],
        "from_100": hosts[100:105],
        "from_150": hosts[150:155],
        "from_200": hosts[200:205],
        "from_250": hosts[250:255],
    }

    for range_name, ips in ip_groups.items():
        print(f"\n[+] Scanning range {range_name}")
        for ip in ips:
            print(f"\n[+] Checking if alive {ip}")
            if ping(ip):
                print(f"\033[1;32m[+] Found {ip} is alive \033[0m")
                return True
    return False


def network_scan(ip_range):
    try:
        network = ipaddress.IPv4Network(ip_range, strict=False)
        total_ips = len(list(network.hosts()))
        progress = 0

        def process_ip(ip):
            with semaphore:
                nonlocal progress
                if ping(ip):
                    with open(ips_file.name, "a") as f:
                        f.write(f"{ip}\n")
                    scan_ports(ip, ports_file)
                with lock:
                    progress += 1
                    show_progress(progress, total_ips)

        threads = []
        for ip in network.hosts():
            thread = threading.Thread(target=process_ip, args=(ip,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        output_queue.put(None)
        print("\n[+] Scan complete.")
    except ValueError as e:
        print(e)
        print("[!] Invalid IP range.")


def show_progress(progress, total):
    percentage = (progress / total) * 100
    bar = ('#' * int(percentage / 2)).ljust(50)
    sys.stdout.write(f"\r[ {bar} ] {percentage:3.0f}% completed")
    sys.stdout.flush()


def process_output():
    while True:
        message = output_queue.get()
        if message is None:
            break
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(message, end="\n")
        sys.stdout.flush()


def main():
    global ips_file, ports_file
    parser = argparse.ArgumentParser(description="Network scanner.")
    parser.add_argument("-i", "--ip", required=True, help="Specify the IP range to scan (e.g., 192.168.1.0/24, 10.0.0.0/16)")
    parser.add_argument("-o", "--output", default="result", help="Base name for the output files (default: 'result')")
    parser.add_argument("-a", "--aggressive", action="store_true", help="Scan live networks immediately")
    args = parser.parse_args()

    with open(f"{args.output}_alive_ips.txt", "w") as input_ips_file, open(f"{args.output}_open_ports.txt", "w") as input_ports_file:
        print(f"[+] Scanning range: {args.ip}")

        output_thread = threading.Thread(target=process_output, daemon=True)
        output_thread.start()

        ips_file = input_ips_file
        ports_file = input_ports_file

        start_scan(args.ip, args.aggressive)

        output_thread.join()


if __name__ == "__main__":
    main()
