import os
import sys
import json
import csv
import argparse
import socket
import hashlib
from datetime import datetime

def banner():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    print(r"""
  ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗     ██╗███╗   ██╗████████╗███████╗██╗      
 ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝     ██║████╗  ██║╚══██╔══╝██╔════╝██║      
 ██║  ███╗███████║██║   ██║███████╗   ██║        ██║██╔██╗ ██║   ██║   █████╗  ██║      
 ██║   ██║██╔══██║██║   ██║╚════██║   ██║        ██║██║╚██╗██║   ██║   ██╔══╝  ██║      
 ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ██╗  ██║██║ ╚████║   ██║   ███████╗███████╗ 
  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝ 
      GHOST-IP-Intel v2.5-PRO (Zero-Guessing Engine)
""")

def compute_sha256(filepath):
    sha = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()
    except Exception:
        return None

def main():
    banner()
    parser = argparse.ArgumentParser(description="GHOST-IP-Intel Enterprise Edition")
    parser.add_argument("--ip", default="ip", help="Path to file containing target IPs")
    parser.add_argument("--json", default="report.json", help="Output JSON report")
    parser.add_argument("--csv", default="report.csv", help="Output CSV report")
    args = parser.parse_args()

    ip_file = args.ip
    if not os.path.exists(ip_file):
        print(f"[-] Error: Target IP file '{ip_file}' not found.")
        return

    file_hash = compute_sha256(ip_file)
    with open(ip_file, 'r', encoding='utf-8', errors='ignore') as f:
        ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    print(f"[+] Loaded {len(ips)} target(s) from '{ip_file}'. Integrity Hash (SHA-256): {file_hash}")
    results = []

    for target in ips:
        print(f"\n[*] Probing target: {target}...")
        open_ports = []
        common_ports = [21, 22, 25, 53, 80, 110, 443, 445, 3306, 3389, 8080]
        for p in common_ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                res = s.connect_ex((target, p))
                if res == 0:
                    open_ports.append(p)
                s.close()
            except Exception:
                pass

        results.append({
            "target": target,
            "open_ports": open_ports,
            "integrity_hash": file_hash,
            "timestamp": datetime.utcnow().isoformat()
        })

    with open(args.json, 'w', encoding='utf-8') as jf:
        json.dump(results, jf, indent=4)
    print(f"\n[+] JSON Report saved to: {args.json}")

    with open(args.csv, 'w', newline='', encoding='utf-8') as cf:
        writer = csv.DictWriter(cf, fieldnames=["target", "open_ports", "integrity_hash", "timestamp"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"[+] CSV Report saved to: {args.csv}")

if __name__ == "__main__":
    main()
