#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SC Osint - Open Source Intelligence Tool
Created for educational and research purposes only.
Author: Your Name (SC Osint)
Version: 1.0
"""

import os
import sys
import time
import socket
import json
import csv
import concurrent.futures
from datetime import datetime
from urllib.parse import quote

try:
    import requests
    from colorama import Fore, Style, init
    import whois
    import phonenumbers
    from phonenumbers import carrier, geocoder, timezone
    import dns.resolver
    from bs4 import BeautifulSoup
    import configparser
except ImportError as e:
    print(f"[!] Missing library: {e}")
    print("[!] Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

init(autoreset=True)

# ==================== COLORS ====================
class Color:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    WHITE = Fore.WHITE
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT

# ==================== CONFIG ====================
def load_config():
    config = configparser.ConfigParser()
    config_file = "config.ini"
    if not os.path.exists(config_file):
        print(f"{Color.RED}[!] config.ini not found. Using defaults.")
        return {
            "proxy": None,
            "timeout": 10,
            "threads": 15,
            "auto_save": True,
            "reports_folder": "Reports",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    config.read(config_file)
    proxy = config.get("SETTINGS", "proxy", fallback="").strip()
    return {
        "proxy": proxy if proxy else None,
        "timeout": config.getint("SETTINGS", "timeout", fallback=10),
        "threads": config.getint("SETTINGS", "threads", fallback=15),
        "auto_save": config.getboolean("SETTINGS", "auto_save", fallback=True),
        "reports_folder": config.get("SETTINGS", "reports_folder", fallback="Reports"),
        "user_agent": config.get("USER_AGENT", "user_agent", fallback="Mozilla/5.0"),
        "whoisxml_api": config.get("API", "whoisxml_api", fallback=""),
        "hunter_api": config.get("API", "hunter_api", fallback=""),
        "numverify_api": config.get("API", "numverify_api", fallback="")
    }

CFG = load_config()

def get_session():
    session = requests.Session()
    session.headers.update({"User-Agent": CFG["user_agent"]})
    if CFG["proxy"]:
        session.proxies = {
            "http": CFG["proxy"],
            "https": CFG["proxy"]
        }
    return session

# ==================== BANNER ====================
def banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"""{Color.CYAN}
    ███████╗ ██████╗     ██████╗ ███████╗██╗███╗   ██╗████████╗
    ██╔════╝██╔════╝    ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
    ███████╗██║         ██║   ██║███████╗██║██╔██╗ ██║   ██║   
    ╚════██║██║         ██║   ██║╚════██║██║██║╚██╗██║   ██║   
    ███████║╚██████╗    ╚██████╔╝███████║██║██║ ╚████║   ██║   
    ╚══════╝ ╚═════╝     ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝   
    {Color.YELLOW}═══════════════════════════════════════════════════════════
    {Color.WHITE}          SC Osint v1.0  |  Open Source Intelligence
    {Color.YELLOW}═══════════════════════════════════════════════════════════
    {Color.GREEN}          Educational & Research purposes only
    {Color.YELLOW}═══════════════════════════════════════════════════════════
    {Color.RESET}""")

# ==================== UTILITIES ====================
def create_reports_folder():
    folder = CFG["reports_folder"]
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def save_report(module_name, target, data):
    if not CFG["auto_save"]:
        return
    folder = create_reports_folder()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/{module_name}_{target}_{timestamp}.txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"SC Osint Report\n")
            f.write(f"Module: {module_name}\n")
            f.write(f"Target: {target}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            if isinstance(data, list):
                for item in data:
                    f.write(str(item) + "\n")
            elif isinstance(data, dict):
                for k, v in data.items():
                    f.write(f"{k}: {v}\n")
            else:
                f.write(str(data))
        print(f"{Color.GREEN}[+] Report saved: {filename}")
    except Exception as e:
        print(f"{Color.RED}[!] Failed to save report: {e}")

def print_info(msg):
    print(f"{Color.CYAN}[*] {Color.WHITE}{msg}")

def print_success(msg):
    print(f"{Color.GREEN}[+] {Color.WHITE}{msg}")

def print_error(msg):
    print(f"{Color.RED}[-] {Color.WHITE}{msg}")

def print_warning(msg):
    print(f"{Color.YELLOW}[!] {Color.WHITE}{msg}")

def input_target(prompt):
    return input(f"{Color.YELLOW}[?] {Color.WHITE}{prompt}: ").strip()

# ==================== USERNAME SEARCH ====================
SOCIAL_SITES = {
    "Instagram": "https://www.instagram.com/{}",
    "Twitter/X": "https://x.com/{}",
    "Facebook": "https://www.facebook.com/{}",
    "GitHub": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "YouTube": "https://www.youtube.com/@{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Tumblr": "https://{}.tumblr.com",
    "Medium": "https://medium.com/@{}",
    "DeviantArt": "https://www.deviantart.com/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Vimeo": "https://vimeo.com/{}",
    "Flickr": "https://www.flickr.com/people/{}",
    "About.me": "https://about.me/{}",
    "Keybase": "https://keybase.io/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "GitLab": "https://gitlab.com/{}",
    "Bitbucket": "https://bitbucket.org/{}",
    "Pastebin": "https://pastebin.com/u/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "Telegram": "https://t.me/{}",
}

def check_username_site(username, site_name, url_template, session):
    url = url_template.format(username)
    try:
        r = session.get(url, timeout=CFG["timeout"], allow_redirects=True)
        if r.status_code == 200:
            # Basic checks for common "not found" patterns
            content = r.text.lower()
            not_found_indicators = ["not found", "doesn't exist", "page not found", "404", "no such user", "user not found"]
            if any(ind in content for ind in not_found_indicators) and r.url == url:
                return site_name, url, False
            return site_name, url, True
        elif r.status_code == 404:
            return site_name, url, False
        else:
            return site_name, url, None  # Unknown
    except Exception:
        return site_name, url, None

def username_search():
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"{Color.CYAN}       USERNAME SEARCH MODULE")
    print(f"{Color.CYAN}{'='*50}\n")
    
    username = input_target("Enter username")
    if not username:
        print_error("Username cannot be empty")
        return

    print_info(f"Searching for username: {username}")
    print_info(f"Checking {len(SOCIAL_SITES)} sites using {CFG['threads']} threads...\n")

    session = get_session()
    found = []
    not_found = []
    unknown = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=CFG["threads"]) as executor:
        futures = {
            executor.submit(check_username_site, username, site, url, session): site
            for site, url in SOCIAL_SITES.items()
        }
        for future in concurrent.futures.as_completed(futures):
            site_name, url, status = future.result()
            if status is True:
                print_success(f"{site_name}: {url}")
                found.append(f"{site_name}: {url}")
            elif status is False:
                print_error(f"{site_name}: Not Found")
                not_found.append(site_name)
            else:
                print_warning(f"{site_name}: Could not determine")
                unknown.append(site_name)

    print(f"\n{Color.GREEN}[+] Found on {len(found)} sites")
    print(f"{Color.RED}[-] Not found on {len(not_found)} sites")
    if unknown:
        print(f"{Color.YELLOW}[!] Unknown status: {len(unknown)} sites")

    report_data = {
        "Username": username,
        "Found": found,
        "Not Found": not_found,
        "Unknown": unknown
    }
    save_report("Username", username, report_data)
    input(f"\n{Color.YELLOW}Press Enter to continue...")

# ==================== PHONE SEARCH ====================
def phone_search():
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"{Color.CYAN}       PHONE NUMBER SEARCH MODULE")
    print(f"{Color.CYAN}{'='*50}\n")

    number = input_target("Enter phone number (with country code, e.g. +201234567890)")
    if not number:
        print_error("Phone number cannot be empty")
        return

    try:
        parsed = phonenumbers.parse(number, None)
        if not phonenumbers.is_valid_number(parsed):
            print_warning("Number may not be valid")
        
        print_info("Analyzing phone number...\n")
        
        info = {
            "Original": number,
            "International Format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "National Format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "E164 Format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "Country Code": parsed.country_code,
            "National Number": parsed.national_number,
            "Carrier": carrier.name_for_number(parsed, "en") or "Unknown",
            "Region": geocoder.description_for_number(parsed, "en") or "Unknown",
            "Timezones": ", ".join(timezone.time_zones_for_number(parsed)) or "Unknown",
            "Is Valid": phonenumbers.is_valid_number(parsed),
            "Is Possible": phonenumbers.is_possible_number(parsed),
            "Number Type": str(phonenumbers.number_type(parsed))
        }

        for k, v in info.items():
            print_success(f"{k}: {v}")

        save_report("Phone", number.replace("+", ""), info)
    except Exception as e:
        print_error(f"Error analyzing number: {e}")

    input(f"\n{Color.YELLOW}Press Enter to continue...")

# ==================== WEBSITE / DOMAIN / IP ====================
def website_search():
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"{Color.CYAN}       WEBSITE / DOMAIN / IP MODULE")
    print(f"{Color.CYAN}{'='*50}\n")

    target = input_target("Enter domain or IP (e.g. example.com or 8.8.8.8)")
    if not target:
        print_error("Target cannot be empty")
        return

    session = get_session()
    results = {"Target": target}

    # DNS Resolution
    print_info("Resolving DNS...")
    try:
        ip = socket.gethostbyname(target)
        results["IP Address"] = ip
        print_success(f"IP Address: {ip}")
    except Exception as e:
        print_error(f"DNS Resolution failed: {e}")
        results["IP Address"] = "Failed"

    # Reverse DNS
    try:
        if "IP Address" in results and results["IP Address"] != "Failed":
            host = socket.gethostbyaddr(results["IP Address"])
            results["Reverse DNS"] = host[0]
            print_success(f"Reverse DNS: {host[0]}")
    except:
        results["Reverse DNS"] = "Not available"

    # Whois
    print_info("Performing Whois lookup...")
    try:
        w = whois.whois(target)
        whois_data = {
            "Domain Name": w.domain_name,
            "Registrar": w.registrar,
            "Creation Date": str(w.creation_date),
            "Expiration Date": str(w.expiration_date),
            "Updated Date": str(w.updated_date),
            "Name Servers": w.name_servers,
            "Status": w.status,
            "Emails": w.emails,
            "Country": getattr(w, "country", "N/A"),
            "Org": getattr(w, "org", "N/A")
        }
        results["Whois"] = whois_data
        for k, v in whois_data.items():
            print_success(f"{k}: {v}")
    except Exception as e:
        print_error(f"Whois failed: {e}")
        results["Whois"] = str(e)

    # DNS Records
    print_info("Fetching DNS records...")
    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
    dns_results = {}
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(target, rtype)
            dns_results[rtype] = [str(rdata) for rdata in answers]
            print_success(f"{rtype}: {dns_results[rtype]}")
        except:
            dns_results[rtype] = "No records"
    results["DNS Records"] = dns_results

    # HTTP Headers
    print_info("Fetching HTTP headers...")
    try:
        r = session.get(f"http://{target}", timeout=CFG["timeout"], allow_redirects=True)
        results["HTTP Status"] = r.status_code
        results["Final URL"] = r.url
        results["Server"] = r.headers.get("Server", "N/A")
        print_success(f"HTTP Status: {r.status_code}")
        print_success(f"Server: {r.headers.get('Server', 'N/A')}")
    except Exception as e:
        print_warning(f"HTTP request failed: {e}")

    save_report("Website", target.replace(".", "_"), results)
    input(f"\n{Color.YELLOW}Press Enter to continue...")

# ==================== EMAIL SEARCH ====================
def email_search():
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"{Color.CYAN}       EMAIL SEARCH MODULE")
    print(f"{Color.CYAN}{'='*50}\n")

    email = input_target("Enter email address")
    if not email or "@" not in email:
        print_error("Invalid email address")
        return

    print_info(f"Analyzing email: {email}\n")
    results = {"Email": email}

    # Basic validation
    username, domain = email.split("@", 1)
    results["Username"] = username
    results["Domain"] = domain

    # Check if domain has MX records
    print_info("Checking MX records...")
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_list = [str(r.exchange) for r in mx_records]
        results["MX Records"] = mx_list
        print_success(f"MX Records found: {mx_list}")
    except Exception as e:
        print_error(f"No MX records or error: {e}")
        results["MX Records"] = "None"

    # Check common providers
    providers = {
        "gmail.com": "Google",
        "yahoo.com": "Yahoo",
        "outlook.com": "Microsoft",
        "hotmail.com": "Microsoft",
        "protonmail.com": "ProtonMail",
        "icloud.com": "Apple",
        "mail.ru": "Mail.ru",
        "yandex.com": "Yandex",
        "aol.com": "AOL"
    }
    results["Provider"] = providers.get(domain.lower(), "Custom / Unknown")
    print_success(f"Provider: {results['Provider']}")

    # Simple Gravatar check
    print_info("Checking Gravatar...")
    import hashlib
    gravatar_hash = hashlib.md5(email.lower().encode()).hexdigest()
    gravatar_url = f"https://www.gravatar.com/avatar/{gravatar_hash}?d=404"
    try:
        r = get_session().get(gravatar_url, timeout=5)
        if r.status_code == 200:
            print_success(f"Gravatar found: https://www.gravatar.com/{gravatar_hash}")
            results["Gravatar"] = f"https://www.gravatar.com/{gravatar_hash}"
        else:
            print_error("No Gravatar found")
            results["Gravatar"] = "Not found"
    except:
        results["Gravatar"] = "Error checking"

    save_report("Email", email.replace("@", "_at_"), results)
    input(f"\n{Color.YELLOW}Press Enter to continue...")

# ==================== GOOGLE DORKS ====================
def google_dorks():
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"{Color.CYAN}       GOOGLE DORKS MODULE")
    print(f"{Color.CYAN}{'='*50}\n")

    target = input_target("Enter target (username / domain / email / keyword)")
    if not target:
        print_error("Target cannot be empty")
        return

    dorks = {
        "General": [
            f'"{target}"',
            f'site:{target}',
            f'inurl:{target}',
            f'intitle:{target}',
            f'intext:{target}',
        ],
        "Files": [
            f'site:{target} ext:pdf',
            f'site:{target} ext:doc OR ext:docx',
            f'site:{target} ext:xls OR ext:xlsx',
            f'site:{target} ext:ppt OR ext:pptx',
            f'site:{target} ext:txt',
            f'site:{target} ext:sql',
            f'site:{target} ext:xml',
            f'site:{target} ext:json',
            f'site:{target} filetype:pdf',
        ],
        "Sensitive": [
            f'site:{target} "password"',
            f'site:{target} "username"',
            f'site:{target} "api_key" OR "apikey"',
            f'site:{target} "secret"',
            f'site:{target} "token"',
            f'site:{target} inurl:admin',
            f'site:{target} inurl:login',
            f'site:{target} inurl:dashboard',
            f'site:{target} "index of"',
        ],
        "Social / People": [
            f'"{target}" site:linkedin.com',
            f'"{target}" site:facebook.com',
            f'"{target}" site:twitter.com OR site:x.com',
            f'"{target}" site:instagram.com',
            f'"{target}" site:github.com',
            f'"{target}" site:pastebin.com',
        ],
        "Images / Media": [
            f'"{target}" site:imgur.com',
            f'"{target}" filetype:jpg OR filetype:png',
        ]
    }

    print_info(f"Generated Google Dorks for: {target}\n")
    all_dorks = []

    for category, queries in dorks.items():
        print(f"{Color.MAGENTA}[{category}]")
        for q in queries:
            encoded = quote(q)
            google_url = f"https://www.google.com/search?q={encoded}"
            print(f"  {Color.GREEN}→ {Color.WHITE}{q}")
            print(f"    {Color.CYAN}{google_url}")
            all_dorks.append(f"{category}: {q} | {google_url}")
        print()

    save_report("Dorks", target.replace(" ", "_"), all_dorks)
    input(f"\n{Color.YELLOW}Press Enter to continue...")

# ==================== PORT SCANNER ====================
def port_scanner():
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"{Color.CYAN}       PORT SCANNER MODULE")
    print(f"{Color.CYAN}{'='*50}\n")

    target = input_target("Enter IP or domain")
    if not target:
        print_error("Target cannot be empty")
        return

    try:
        ip = socket.gethostbyname(target)
        print_success(f"Resolved {target} → {ip}")
    except Exception as e:
        print_error(f"Could not resolve target: {e}")
        return

    print_info("Select scan type:")
    print("  1. Quick scan (common ports)")
    print("  2. Full scan (1-1024)")
    print("  3. Custom ports")
    choice = input(f"{Color.YELLOW}[?] Choice: ").strip()

    if choice == "1":
        ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080, 8443]
    elif choice == "2":
        ports = list(range(1, 1025))
    elif choice == "3":
        custom = input_target("Enter ports separated by comma (e.g. 80,443,8080)")
        try:
            ports = [int(p.strip()) for p in custom.split(",")]
        except:
            print_error("Invalid ports")
            return
    else:
        print_error("Invalid choice")
        return

    print_info(f"Scanning {len(ports)} ports on {ip}...\n")
    open_ports = []

    def scan_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return port
        except:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(scan_port, port): port for port in ports}
        for future in concurrent.futures.as_completed(futures):
            port = future.result()
            if port:
                print_success(f"Port {port} is OPEN")
                open_ports.append(port)

    if open_ports:
        print(f"\n{Color.GREEN}[+] Open ports: {sorted(open_ports)}")
    else:
        print_warning("No open ports found")

    save_report("PortScan", target.replace(".", "_"), {"Target": target, "IP": ip, "Open Ports": open_ports})
    input(f"\n{Color.YELLOW}Press Enter to continue...")

# ==================== PROXY CHECKER ====================
def proxy_info():
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"{Color.CYAN}       PROXY / ANONYMITY MODULE")
    print(f"{Color.CYAN}{'='*50}\n")

    if CFG["proxy"]:
        print_success(f"Current proxy configured: {CFG['proxy']}")
    else:
        print_warning("No proxy configured in config.ini")

    print_info("Checking your current public IP...\n")
    try:
        session = get_session()
        r = session.get("https://api.ipify.org?format=json", timeout=10)
        ip_data = r.json()
        print_success(f"Public IP: {ip_data.get('ip')}")

        # More info
        r2 = session.get(f"https://ipinfo.io/{ip_data.get('ip')}/json", timeout=10)
        info = r2.json()
        for k in ["city", "region", "country", "org", "timezone"]:
            if k in info:
                print_success(f"{k.capitalize()}: {info[k]}")
    except Exception as e:
        print_error(f"Failed to get IP info: {e}")

    input(f"\n{Color.YELLOW}Press Enter to continue...")

# ==================== MAIN MENU ====================
def main_menu():
    while True:
        banner()
        print(f"""{Color.WHITE}
    {Color.CYAN}[1]{Color.WHITE}  Username Search          {Color.CYAN}[6]{Color.WHITE}  Port Scanner
    {Color.CYAN}[2]{Color.WHITE}  Phone Number Search      {Color.CYAN}[7]{Color.WHITE}  Proxy / IP Info
    {Color.CYAN}[3]{Color.WHITE}  Website / Domain / IP    {Color.CYAN}[8]{Color.WHITE}  About
    {Color.CYAN}[4]{Color.WHITE}  Email Search             {Color.CYAN}[0]{Color.WHITE}  Exit
    {Color.CYAN}[5]{Color.WHITE}  Google Dorks
        """)
        
        choice = input(f"{Color.YELLOW}[?] Select option: ").strip()

        if choice == "1":
            username_search()
        elif choice == "2":
            phone_search()
        elif choice == "3":
            website_search()
        elif choice == "4":
            email_search()
        elif choice == "5":
            google_dorks()
        elif choice == "6":
            port_scanner()
        elif choice == "7":
            proxy_info()
        elif choice == "8":
            about()
        elif choice == "0":
            print(f"\n{Color.GREEN}[+] Thank you for using SC Osint. Goodbye!\n")
            sys.exit(0)
        else:
            print_error("Invalid option")
            time.sleep(1)

def about():
    print(f"""
{Color.CYAN}{'='*50}
       ABOUT SC OSINT
{'='*50}{Color.WHITE}

  Name        : SC Osint
  Version     : 1.0
  Type        : Open Source Intelligence Tool
  Language    : Python 3
  Purpose     : Educational & Research only

  Features:
    • Username Search across social platforms
    • Phone Number Analysis
    • Domain / IP / Whois Lookup
    • Email Investigation
    • Google Dorks Generator
    • Port Scanner
    • Proxy Support
    • Automatic Report Saving

  Disclaimer:
    This tool is for educational and legitimate
    research purposes only. The author is not
    responsible for any misuse.

{Color.CYAN}{'='*50}{Color.RESET}
    """)
    input(f"{Color.YELLOW}Press Enter to continue...")

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    try:
        create_reports_folder()
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Color.RED}[!] Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Color.RED}[!] Unexpected error: {e}")
        sys.exit(1)
