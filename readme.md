# InetScan

This project is a Python-based network scanning tool that identifies active devices and open ports within a range of IP addresses. It uses `fping` to check host availability and `nc` to probe open ports.

## Features

- **Concurrent Ping**: Quickly checks which devices are active.
- **Port Scanning**: Scans a predefined list of common ports.
- **Progress Bar**: Displays real-time scanning progress.
- **Output Files**:
  - List of active IP addresses.
  - List of IPs and their open ports.
- Optimized with multithreading for faster performance.

## Requirements

1. Python 3.x
2. External tools:
   - `fping`: To ping multiple IP addresses.
   - `nc` (Netcat): To scan ports.

## Installing Dependencies

On Linux-based systems, you can install the required tools with:

```bash
sudo apt update
sudo apt install fping netcat
```

## Usage

### Run the script as follows:

```bash
python scanner.py -i <IP_range> -o <base_filename>
```

### Example:

```bash
python scanner.py -i 192.168.1.0/24 -o results
```

### This command will:

- Scan all IPs in the range 192.168.1.0/24.
- Save active IP addresses to results_active_ips.txt.
- Save open ports to results_open_ports.txt.

### Output Files

1.  results_active_ips.txt: Contains a list of detected active IP addresses.
2.  results_open_ports.txt: Lists IPs and their open ports.

## Customization
- Changing the Number of Threads

- By default, the script uses 80 threads for scanning. You can modify this variable in the source code:
    ```
    max_threads = 30
    ```
    Modifying Ports to Scan
    
    The list of ports is defined in the code:
    ```
    ports = [21, 23, 25, 79, 80, 88, 135, 443, 445, 2375, 2376, 8080, 8081]
    ```
    Add or remove ports according to your needs.

## Notes


This script is intended for use on internal networks or with the explicit permission of the network owner. Do not use it on unauthorized networks.
Requires permissions to install and execute external tools (fping, nc).

## Contributions

Contributions are welcome! If you encounter any issues or have an improvement to propose, feel free to open an issue or submit a pull request.
