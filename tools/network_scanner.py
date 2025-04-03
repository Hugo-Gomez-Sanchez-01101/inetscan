from rich.console import Console
import threading
import ipaddress
import subprocess


class Network_Scanner:
    def __init__(self, max_threads):
        self.console = Console()
        self.max_threads = max_threads
        self.network_map = []
        self.lock = threading.Lock()

    def scan_networks(self, networks, ports):
        self.networks = networks  # Corrección de `netkorks`
        self.ports = ports

        def scan_network_hosts(network_str):
            network = ipaddress.IPv4Network(network_str, strict=False)
            local_results = []
            for host in network.hosts():
                open_ports = self.scan_ports(host)  # Agregado `self.`
                local_results.append({"host": str(host), "open_ports": open_ports})
            with self.lock:  # Agregado `self.`
                self.network_map.extend(local_results)

        threads = []
        for network in self.networks:
            thread = threading.Thread(target=scan_network_hosts, args=(network,))
            threads.append(thread)
            thread.start()

            if len(threads) >= self.max_threads:
                for t in threads:
                    t.join()
                threads.clear()

        for thread in threads:
            thread.join()

        return self.network_map

    def scan_ports(self, ip):
        open_ports = []
        for port in self.ports:
            try:
                result = subprocess.run(['nc', '-z', '-w1', str(ip), str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    open_ports.append(port)
            except Exception:
                pass
        return open_ports
