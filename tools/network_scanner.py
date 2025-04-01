from rich.console import Console
import threading
import ipaddress


ports = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]
console = Console()
#implementar esto:
max_threads = 30


def scan_networks(networks):
    network_map = []

    def scan_network_hosts(network_str):
        network = ipaddress.IPv4Network(network_str, strict=False)
        for host in network.hosts():
            ports = scan_ports(host)
            network_map.append({"host": str(host), "open_ports": ports})

    threads = []
    for network in networks:
        thread = threading.Thread(target=scan_network_hosts, args=(network,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return network_map


def scan_ports(ip):
    open_ports = []
    
    for port in ports:
        try:
            result = subprocess.run(['nc', '-z', '-w1', str(ip), str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                open_ports.append(port)
        except Exception:
            pass
    
    return open_ports