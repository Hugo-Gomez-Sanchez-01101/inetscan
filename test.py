import ipaddress

def subdividir_red(ip_red):
    red = ipaddress.IPv4Network(ip_red, strict=False)
    
    if red.prefixlen < 24:
        subredes = list(red.subnets(new_prefix=24))
    else:
        subredes = [red]
    
    return [str(subred) for subred in subredes]

# Ejemplos de uso
#print(subdividir_red("192.168.0.0/16"))  # Genera todas las /24 dentro del /16
print(subdividir_red("10.0.0.0/8"))      # Genera todas las /24 dentro del /8
#print(subdividir_red("172.16.5.0/24"))   # Solo devuelve ["172.16.5.0/24"]
