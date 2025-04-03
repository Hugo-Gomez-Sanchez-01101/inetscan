from rich.console import Console
from queue import Queue
import subprocess
import ipaddress
import threading
import sys

class Network_Verifyer:
    
    def __init__(self, max_threads):
        self.lock = threading.Lock()
        self.output_queue = Queue()
        self.processed_ips = set()
        self.console = Console()
        self.error_console = Console(stderr=True)
        self.max_threads = max_threads

    def verify_network(self, ip, aggressive, timeout):
        subnet_ranges = self.get_subnet_ranges(ip)
        alive_ranges = []

        def check_range(subnet):
            if self.range_exists(subnet, timeout):
                self.console.print(f"[bold green][+] Subnet {subnet} is alive[/bold green]")
                alive_ranges.append(subnet)
            else:
                self.error_console.print(f"[bold red][-] Subnet {subnet} is not alive[/bold red]")
        
        threads = []
        for subnet in subnet_ranges:
            if aggressive:
                thread = threading.Thread(target=check_range, args=(subnet,))
                threads.append(thread)
                thread.start()
            else:
                check_range(subnet)
        
        for thread in threads:
            thread.join()

        return alive_ranges

    def get_subnet_ranges(self, network_ip):
        network = ipaddress.IPv4Network(network_ip, strict=False)
        return [str(subnet) for subnet in (network.subnets(new_prefix=24) if network.prefixlen < 24 else [network])]

    def ping(self, ip, timeout):
        try:
            command = ['fping', '-a', '-q', str(ip)]
            if timeout is not None:
                command.extend(['-t', str(timeout)])
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False

    def range_exists(self, network, timeout):
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

        def check_ip(ip):
            nonlocal alive
            if self.ping(ip, timeout):
                with self.lock:
                    alive = True

        threads = []
        for _, ips in ip_groups.items():
            for ip in ips:
                thread = threading.Thread(target=check_ip, args=(ip,))
                threads.append(thread)
                thread.start()
                
                if len(threads) >= self.max_threads:
                    for t in threads:
                        t.join()
                    threads.clear()

        for thread in threads:
            thread.join()

        return alive