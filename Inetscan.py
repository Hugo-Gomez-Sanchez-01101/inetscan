import argparse
import ipaddress
import subprocess
import threading
import sys
from queue import Queue

max_hilos = 30
puertos = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]
ips_procesadas = set()
lock = threading.Lock()
cola_salida = Queue()


def ping(ip):
    try:
        result = subprocess.run(['fping', '-a', '-q', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            with lock:
                if ip not in ips_procesadas:
                    ips_procesadas.add(ip)
                    cola_salida.put(f"\033[1;32m[+] {ip} is alive\033[0m")
                    return True
    except Exception:
        pass
    return False


def escanear_puertos(ip, archivo_puertos):
    for puerto in puertos:
        try:
            result = subprocess.run(['nc', '-z', '-w1', str(ip), str(puerto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                with lock:
                    cola_salida.put(f"\033[1;32m[+] {ip}:{puerto} open \033[0m")
                    archivo_puertos.write(f"{ip}:{puerto}\n")
        except Exception:
            pass


def range_exist(network):
    hosts = list(network.hosts())
    ip_groups = {
        "first_5": hosts[:5],
        "from_50": hosts[50:55], 
        "from_100": hosts[100:105],
        "from_150": hosts[150:155],
        "from_160": hosts[160:165],
        "from_200": hosts[200:205],
        "from_250": hosts[250:255],
    }

    for range_ips, ips in ip_groups.items():
        print(f"\n[+] Scaning range {range_ips}")
        for ip in ips:
            print(f"\n[+] Checking if alive {ip}")
            if(ping(ip)):
                print(f"\033[1;32m[+] Found {ip} is alive \033[0m")
                return True
    
    return False


def range_scan(ip_range, archivo_ips, archivo_puertos):
    try:
        network = ipaddress.IPv4Network(ip_range, strict=False)

        if range_exist(network):
            total_ips = len(list(network.hosts()))
            progreso = 0
            def process_ip(ip):
                print(ip)
                nonlocal progreso
                if ping(ip):
                    with open(archivo_ips.name, "a") as f:
                        f.write(f"{ip}\n")
                    escanear_puertos(ip, archivo_puertos)
                with lock:
                    progreso += 1
                    mostrar_progreso(progreso, total_ips)

            threads = []
            for ip in network.hosts():
                while len(threads) >= max_hilos:
                    threads = [t for t in threads if t.is_alive()]
                
                thread = threading.Thread(target=process_ip, args=(ip,))
                threads.append(thread)
                thread.start()

            for t in threads:
                t.join()
        else:
            print("[-] range x discarded.")
        cola_salida.put(None)
        print("\n[+] Scan complete.")
    except ValueError as e:
        print(e)
        print("[!] Invalid IP range.")


#Visual
def mostrar_progreso(progreso, total):
    porcentaje = (progreso / total) * 100
    barra = ('#' * int(porcentaje / 2)).ljust(50)
    sys.stdout.write(f"\r[ {barra} ] {porcentaje:3.0f}% completed")
    sys.stdout.flush()

def procesar_salida():
    while True:
        mensaje = cola_salida.get()
        if mensaje is None:
            break
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(mensaje, end="\n")
        sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="Escáner de redes.")
    parser.add_argument("-i", "--ip", required=True, help="Especifica el rango de IP para escanear (ej. 192.168.1.0/24, 10.0.0.0/16)")
    parser.add_argument("-o", "--output", default="resultado", help="Nombre base del archivo de salida (por defecto: 'resultado')")
    args = parser.parse_args()

    with open(f"{args.output}_ips_vivas.txt", "w") as archivo_ips, open(f"{args.output}_puertos_abiertos.txt", "w") as archivo_puertos:
        print(f"[+] Escaneando el rango: {args.ip}")
        
        salida_thread = threading.Thread(target=procesar_salida, daemon=True)
        salida_thread.start()

        range_scan(args.ip, archivo_ips, archivo_puertos)

        salida_thread.join()

if __name__ == "__main__":
    main()
