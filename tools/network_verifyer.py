def verify_networks(ip, output_file, aggressive, timeout):
    subnet_ranges = get_subnet_ranges(ip)
    alive_ranges = []

    def check_range(subnet):
        if range_exists(subnet, timeout):
            console.print(f"[bold green][+] Subnet {subnet} is alive[/bold green]")
            alive_ranges.append(subnet)
        else:
            console.print(f"[bold red][-] Subnet {subnet} is not alive[/bold red]")
    
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
    
    console.print("\n[bold yellow]Network/s Verified! Results:[/bold yellow]", alive_ranges)
    
    with open(output_file, "w") as f:
        f.write("\n".join(alive_ranges) + "\n")

    return alive_ranges

def get_subnet_ranges(network_ip):
    network = ipaddress.IPv4Network(network_ip, strict=False)
    return [str(subnet) for subnet in (network.subnets(new_prefix=24) if network.prefixlen < 24 else [network])]

def ping(ip, timeout):
    try:
        command = ['fping', '-a', '-q', str(ip)]
        if timeout is not None:
            command.extend(['-t', str(timeout)])
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

def range_exists(network, timeout):
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
        if ping(ip, timeout):
            alive = True
            console.print(f"[bold green][+] {ip} is alive[/bold green]")

    threads = []
    for range_name, ips in ip_groups.items():
        for ip in ips:
            thread = threading.Thread(target=check_ip, args=(ip,))
            threads.append(thread)
            thread.start()
            
            if len(threads) >= max_threads:
                for t in threads:
                    t.join()
                threads.clear()

    for thread in threads:
        thread.join()

    return alive


