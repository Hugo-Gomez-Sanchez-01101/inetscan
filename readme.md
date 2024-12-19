# Escáner de Redes

Este proyecto es una herramienta de escaneo de redes en Python que permite identificar dispositivos activos y puertos abiertos en un rango de direcciones IP. Utiliza `fping` para verificar la disponibilidad de hosts y `nc` para comprobar puertos abiertos.

## Características

- **Ping concurrente**: Verifica rápidamente qué dispositivos están activos.
- **Escaneo de puertos**: Escanea una lista predefinida de puertos comunes.
- **Barra de progreso**: Muestra el progreso del escaneo en tiempo real.
- **Salida en archivos**:
  - Lista de direcciones IP activas.
  - Lista de IPs y sus puertos abiertos.
- Optimizado con múltiples hilos para un rendimiento más rápido.

## Requisitos

1. Python 3.x
2. Herramientas externas:
   - `fping`: Para realizar el ping a múltiples direcciones IP.
   - `nc` (Netcat): Para escanear puertos.

### Instalación de dependencias

En sistemas basados en Linux, puedes instalar las herramientas requeridas con:

```bash
sudo apt update
sudo apt install fping netcat
```

### Uso

Ejecuta el script de la siguiente manera:

```bash
python escaner.py -i <rango_de_IP> -o <nombre_archivo_base>
```
Ejemplo:
```bash
python escaner.py -i 192.168.1.0/24 -o resultados
```


Este comando:

    Escaneará todas las IPs en el rango 192.168.1.0/24.
    Guardará las direcciones IP activas en resultados_ips_vivas.txt.
    Guardará los puertos abiertos en resultados_puertos_abiertos.txt.

Archivos de Salida

    resultados_ips_vivas.txt: Contiene una lista de las direcciones IP activas encontradas.
    resultados_puertos_abiertos.txt: Lista de IPs y sus puertos abiertos.

Personalización
Cambiar el número de hilos

Por defecto, el script utiliza 80 hilos para escanear. Puedes modificar esta variable en el código fuente:

max_hilos = 30

Modificar los puertos a escanear

La lista de puertos está definida en el código:

puertos = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]

Agrega o elimina puertos según tus necesidades.
Notas

    Este script está diseñado para ser utilizado en redes internas o con permiso explícito del propietario. No lo uses en redes sin autorización.
    Requiere permisos para instalar y ejecutar herramientas externas (fping, nc).

### Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún problema o tienes una mejora, abre un issue o envía un pull request.
