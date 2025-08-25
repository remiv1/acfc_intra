# Script PowerShell pour générer des certificats SSL réels
# Nécessite OpenSSL installé

# Installation d'OpenSSL (si nécessaire) :
# Télécharger depuis : https://slproweb.com/products/Win32OpenSSL.html
# Ou utiliser Chocolatey : choco install openssl

# Génération du certificat auto-signé :
# openssl req -x509 -newkey rsa:4096 -keyout server.key.pem -out server.crt.pem -days 365 -nodes -subj "/C=FR/ST=France/L=Paris/O=ACFC/OU=IT Department/CN=localhost"

# Pour un certificat avec plusieurs domaines :
# openssl req -x509 -newkey rsa:4096 -keyout server.key.pem -out server.crt.pem -days 365 -nodes -subj "/C=FR/ST=France/L=Paris/O=ACFC/OU=IT Department/CN=localhost" -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"

# Vérification du certificat :
# openssl x509 -in server.crt.pem -text -noout
