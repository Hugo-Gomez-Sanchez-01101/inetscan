ports = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]

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