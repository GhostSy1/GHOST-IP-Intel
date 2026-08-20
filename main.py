import os
import sys
import json
import csv
import socket
import ssl
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

VERSION = "GHOST-IP-Intel v2.2-PRO (Strict Anti-Proxy Engine)"

BANNER = f"""
[bold cyan] ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗     ██╗███╗   ██╗████████╗███████╗██╗     [/bold cyan]
[bold cyan]██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝     ██║████╗  ██║╚══██╔══╝██╔════╝██║     [/bold cyan]
[bold white]██║  ███╗███████║██║   ██║███████╗   ██║        ██║██╔██╗ ██║   ██║   █████╗  ██║     [/bold white]
[bold white]██║   ██║██╔══██║██║   ██║╚════██║   ██║        ██║██║╚██╗██║   ██║   ██╔══╝  ██║     [/bold white]
[bold blue]╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ██╗  ██║██║ ╚████║   ██║   ███████╗███████╗[/bold blue]
[bold blue] ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝[/bold blue]
[bold yellow]     {VERSION}[/bold yellow]
"""

console = Console()

def load_targets(ip_file):
    if not ip_file or not os.path.exists(ip_file):
        console.print(f"[bold red][!] Error: Target IP file '{ip_file}' is mandatory![/bold red]")
        sys.exit(1)
    
    content = None
    for enc in ['utf-8-sig', 'utf-8', 'utf-16', 'cp1256', 'latin-1']:
        try:
            with open(ip_file, 'r', encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
            
    if content is None:
        with open(ip_file, 'rb') as f:
            raw = f.read()
        for enc in ['utf-16', 'utf-8', 'cp1256', 'latin-1']:
            try:
                content = raw.decode(enc)
                break
            except:
                continue
                
    if not content:
        console.print(f"[bold red][!] Error: Could not read target file '{ip_file}' due to encoding issues.[/bold red]")
        sys.exit(1)
        
    targets = []
    for line in content.splitlines():
        clean_line = line.replace('\x00', '').strip()
        if clean_line and not clean_line.startswith("#"):
            targets.append(clean_line)
            
    if not targets:
        console.print(f"[bold red][!] Error: Target file '{ip_file}' contains no valid IPv4 addresses![/bold red]")
        sys.exit(1)
    return targets

def query_dns(target_ip):
    try:
        hostnames = socket.gethostbyaddr(target_ip)
        return hostnames[0], "Verified PTR Record"
    except socket.herror:
        return "Unknown", "No PTR Record Found"

def probe_service(target_ip, port):
    """
    Strict Anti-Proxy probe:
    Does not trust socket.connect_ex alone (which can be faked by firewall SYN proxies).
    Requires actual application-layer verification (banner reception or HTTP response).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        res = s.connect_ex((target_ip, port))
        if res != 0:
            s.close()
            return None, None

        # Connected at TCP level. Now verify application layer responsiveness to filter SYN proxies.
        banner = None
        
        # 1. Try receiving initial banner (FTP, SSH, SMTP, etc.)
        try:
            s.settimeout(1.5)
            data = s.recv(1024)
            if data:
                decoded = data.decode('utf-8', errors='ignore').strip()
                if decoded:
                    banner = f"Live Banner: {decoded.replace(chr(10), ' ').replace(chr(13), ' ')}"
        except socket.timeout:
            pass
        except:
            pass

        # 2. If no initial banner and it's a web/secure port, send a test HTTP request to verify actual service
        if not banner and port in [80, 443, 8080, 8443]:
            try:
                if port in [443, 8443]:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    ss = context.wrap_socket(s, server_hostname=target_ip)
                    ss.settimeout(2.0)
                    ss.sendall(b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n")
                    resp = ss.recv(512)
                    ss.close()
                    if resp:
                        banner = "Verified HTTPS Web Service"
                else:
                    s.settimeout(2.0)
                    s.sendall(b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n")
                    resp = s.recv(512)
                    s.close()
                    if resp:
                        banner = "Verified HTTP Web Service"
            except:
                pass

        s.close()
        
        # If socket connected but absolutely NO application response / banner / data was exchanged,
        # it is likely a firewall SYN proxy trap. Discard it as filtered/closed.
        if not banner:
            return None, None
            
        return port, banner
    except:
        pass
    return None, None

def asset_recon(target_ip):
    analysis = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": VERSION,
        "ip": target_ip,
        "reverse_dns": "Unknown",
        "open_ports": [],
        "port_banners": {},
        "note": "Strict application-layer verification. Firewall SYN proxies filtered."
    }
    
    ptr, _ = query_dns(target_ip)
    analysis["reverse_dns"] = ptr
    
    ports = [21, 22, 25, 53, 80, 110, 443, 445, 3306, 3389, 8080, 8443]
    open_ports = []
    banners = {}
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(probe_service, target_ip, p): p for p in ports}
        for fut in as_completed(futures):
            p, b = fut.result()
            if p:
                open_ports.append(p)
                banners[str(p)] = b
                
    analysis["open_ports"] = sorted(open_ports)
    analysis["port_banners"] = banners
    return analysis

def save_reports(results, json_out, csv_out):
    if json_out:
        with open(json_out, 'w', encoding='utf-8') as jf:
            json.dump(results, jf, indent=4)
        console.print(f"[bold green][+] JSON Report saved to: {json_out}[/bold green]")
    if csv_out:
        with open(csv_out, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.writer(cf)
            writer.writerow(["Timestamp", "Version", "Target IP", "Reverse DNS", "Open Ports", "Port Details"])
            for r in results:
                writer.writerow([r["timestamp"], r["version"], r["ip"], r["reverse_dns"], ", ".join(map(str, r["open_ports"])), json.dumps(r["port_banners"])])
        console.print(f"[bold green][+] CSV Report saved to: {csv_out}[/bold green]")

def main():
    parser = argparse.ArgumentParser(description="GHOST-IP-Intel v2.2-PRO")
    parser.add_argument("--ip", default="ip", help="Path to authorized targets file (default: ip)")
    parser.add_argument("--target", help="Optional single target override")
    parser.add_argument("--json", help="Export to JSON")
    parser.add_argument("--csv", help="Export to CSV")
    args = parser.parse_args()

    console.print(Panel(BANNER, border_style="cyan", expand=False))
    
    targets = load_targets(args.ip)
    if args.target:
        if args.target not in targets:
            console.print(f"[bold red][!] Target {args.target} not in authorized file '{args.ip}'![/bold red]")
            sys.exit(1)
        targets = [args.target]

    console.print(f"[bold green][+] Loaded {len(targets)} target(s) from '{args.ip}'. Running {VERSION}...[/bold green]")
    
    results = []
    for t_ip in targets:
        try:
            socket.inet_pton(socket.AF_INET, t_ip)
        except socket.error:
            console.print(f"[bold red][!] Invalid IPv4: {t_ip}[/bold red]")
            continue
            
        console.print(f"\n[bold yellow][*] Probing target: {t_ip} (Strict Anti-Proxy Mode)...[/bold yellow]")
        res = asset_recon(t_ip)
        results.append(res)
        
        table = Table(title=f"GHOST Report: {t_ip}", border_style="cyan")
        table.add_column("Field", style="yellow")
        table.add_column("Observation", style="white")
        table.add_row("Target IP", res["ip"])
        table.add_row("Reverse DNS", res["reverse_dns"])
        table.add_row("Open Ports", ", ".join(map(str, res["open_ports"])) if res["open_ports"] else "None (All filtered or SYN-proxy dropped)")
        for port, banner in res["port_banners"].items():
            table.add_row(f"Port {port}", banner)
        console.print(table)

    save_reports(results, args.json, args.csv)
    console.print("\n[bold green][+] Done. Zero fake ports displayed.[/bold green]")

if __name__ == "__main__":
    main()
