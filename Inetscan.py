import argparse
import ipaddress
import subprocess
import threading
import sys
from queue import Queue

max_hilos = 80
puertos = [21, 22, 23, 25, 79, 80, 88, 135, 3389, 443, 445, 873, 2049, 2375, 2376, 8080, 8081]
ips_procesadas = set()
lock = threading.Lock()
cola_salida = Queue()

def hacer_ping(ip):
    try:
        result = subprocess.run(['fping', '-a', '-q', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            with lock:
                if ip not in ips_procesadas:
                    ips_procesadas.add(ip)
                    cola_salida.put(f"\033[1;32m[+] {ip} está viva\033[0m")
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
                    cola_salida.put(f"\033[1;32m[+] {ip}:{puerto} abierto \033[0m")
                    archivo_puertos.write(f"{ip}:{puerto}\n")
        except Exception:
            pass

def mostrar_progreso(progreso, total):
    porcentaje = (progreso / total) * 100
    barra = ('#' * int(porcentaje / 2)).ljust(50)
    sys.stdout.write(f"\r[ {barra} ] {porcentaje:3.0f}% completado")
    sys.stdout.flush()

def procesar_salida():
    while True:
        mensaje = cola_salida.get()
        if mensaje is None:  # Señal para terminar
            break
        sys.stdout.write("\r" + " " * 80 + "\r")  # Limpia la línea
        print(mensaje, end="\n")
        sys.stdout.flush()

def validar_rangos(ip_range):
    try:
        network = ipaddress.IPv4Network(ip_range, strict=False)
        rangos_validos = []

        def validar_subred(subnet):
            for host in list(subnet.hosts())[:5]:  # Primeras 5 IPs de hosts
                print(host)
                if hacer_ping(host):
                    rangos_validos.append(subnet)
                    break

        threads = []
        for subnet in network.subnets(new_prefix=24):  # Subredes del rango original
            while len(threads) >= max_hilos:
                for t in threads:
                    if not t.is_alive():
                        threads.remove(t)
            thread = threading.Thread(target=validar_subred, args=(subnet,))
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()

        return rangos_validos

    except ValueError:
        print("\033[1;31m[!] Rango de IP no válido.\033[0m")
        return []

def escanear_red(rangos_validos, archivo_ips, archivo_puertos):
    total_ips = sum(len(list(r.hosts())) for r in rangos_validos)
    progreso = 0

    def procesar_ip(ip):
        nonlocal progreso
        if hacer_ping(ip):
            with open(archivo_ips.name, "a") as f:
                f.write(f"{ip}\n")
            escanear_puertos(ip, archivo_puertos)
        with lock:
            progreso += 1
            mostrar_progreso(progreso, total_ips)

    threads = []
    for rango in rangos_validos:
        for ip in rango.hosts():
            while len(threads) >= max_hilos:
                for t in threads:
                    if not t.is_alive():
                        threads.remove(t)
            thread = threading.Thread(target=procesar_ip, args=(ip,))
            threads.append(thread)
            thread.start()

    for t in threads:
        t.join()

    cola_salida.put(None)  # Señal para finalizar el hilo de salida
    print("\n\033[1;33m[!] \033[1mEscaneo completo.\033[0m")

def main():
    parser = argparse.ArgumentParser(description="Escáner de redes.")
    parser.add_argument("-i", "--ip", required=True, help="Especifica el rango de IP para escanear (ej. 192.168.1.0/24, 10.0.0.0/8)")
    parser.add_argument("-o", "--output", default="resultado", help="Nombre base del archivo de salida (por defecto: 'resultado')")
    args = parser.parse_args()

    with open(f"{args.output}_ips_vivas.txt", "w") as archivo_ips, open(f"{args.output}_puertos_abiertos.txt", "w") as archivo_puertos:
        print(f"\033[1;33m[!] \033[0m\033[1;33mValidando rangos en: {args.ip}\033[0m")

        salida_thread = threading.Thread(target=procesar_salida, daemon=True)
        salida_thread.start()

        rangos_validos = validar_rangos(args.ip)

        if not rangos_validos:
            print("\033[1;31m[!] No se encontraron rangos válidos.\033[0m")
            cola_salida.put(None)
            return

        print(f"\033[1;33m[!] \033[0m\033[1;33m{len(rangos_validos)} rangos válidos encontrados. Iniciando escaneo...\033[0m")
        escanear_red(rangos_validos, archivo_ips, archivo_puertos)

        salida_thread.join()

if __name__ == "__main__":
    main()
