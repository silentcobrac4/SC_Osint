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

# ==================== USERNAME SEARCH (IMPROVED) ====================
SOCIAL_SITES = {
    # Social Media
    "Instagram": "https://www.instagram.com/{}/",
    "Twitter/X": "https://x.com/{}",
    "Facebook": "https://www.facebook.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "YouTube": "https://www.youtube.com/@{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "Snapchat": "https://www.snapchat.com/add/{}",
    "Threads": "https://www.threads.net/@{}",
    
    # Developers
    "GitHub": "https://github.com/{}",
    "GitLab": "https://gitlab.com/{}",
    "Bitbucket": "https://bitbucket.org/{}",
    "StackOverflow": "https://stackoverflow.com/users/{}",
    "HackerRank": "https://www.hackerrank.com/{}",
    "LeetCode": "https://leetcode.com/{}",
    "CodePen": "https://codepen.io/{}",
    "Replit": "https://replit.com/@{}",
    "Dev.to": "https://dev.to/{}",
    
    # Gaming
    "Steam": "https://steamcommunity.com/id/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Xbox": "https://xboxgamertag.com/search/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Minecraft": "https://namemc.com/profile/{}",
    
    # Creative / Media
    "Medium": "https://medium.com/@{}",
    "DeviantArt": "https://www.deviantart.com/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Flickr": "https://www.flickr.com/people/{}",
    "Vimeo": "https://vimeo.com/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    
    # Other
    "Tumblr": "https://{}.tumblr.com",
    "About.me": "https://about.me/{}",
    "Keybase": "https://keybase.io/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "Pastebin": "https://pastebin.com/u/{}",
    "Telegram": "https://t.me/{}",
    "VK": "https://vk.com/{}",
    "Quora": "https://www.quora.com/profile/{}",
    "ProductHunt": "https://www.producthunt.com/@{}",
    "AngelList": "https://angel.co/u/{}",
    "CashApp": "https://cash.app/${}",
    "OnlyFans": "https://onlyfans.com/{}",
}

# Site-specific not-found indicators for higher accuracy
SITE_NOT_FOUND = {
    "Instagram": ["sorry, this page isn't available", "page not found"],
    "Twitter/X": ["this account doesn’t exist", "account suspended", "page doesn’t exist"],
    "GitHub": ["not found", "404"],
    "Reddit": ["sorry, nobody on reddit goes by that name", "page not found"],
    "TikTok": ["couldn't find this account", "page not available"],
    "YouTube": ["this page isn't available", "404"],
    "Twitch": ["sorry. unless you’ve got a time machine", "404"],
    "Steam": ["the specified profile could not be found"],
    "Telegram": ["if you have telegram, you can contact"],
}

def check_username_site(username, site_name, url_template, session):
    url = url_template.format(username)
    try:
        headers = {
            "User-Agent": CFG["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        r = session.get(url, timeout=CFG["timeout"], allow_redirects=True, headers=headers)
        
        content = r.text.lower()
        final_url = r.url.lower()

        # Strong 404
        if r.status_code == 404:
            return site_name, url, False

        # Site-specific checks
        if site_name in SITE_NOT_FOUND:
            for indicator in SITE_NOT_FOUND[site_name]:
                if indicator in content:
                    return site_name, url, False

        # General not-found indicators
        general_not_found = [
            "page not found", "not found", "doesn't exist", "does not exist",
            "user not found", "no such user", "account not found",
            "profile not found", "this page isn't available", "sorry, this page",
            "couldn't find", "nobody on reddit goes by that name"
        ]
        
        if any(ind in content for ind in general_not_found):
            return site_name, url, False

        # If status 200 and no not-found indicators → likely exists
        if r.status_code == 200:
            return site_name, url, True

        # Redirects to login or error pages often mean not found
        if "login" in final_url or "error" in final_url or "404" in final_url:
            return site_name, url, False

        return site_name, url, None  # Unknown
    except Exception:
        return site_name, url, None

def username_search():
    print(f"\n{Color.CYAN}{'='*55}")
    print(f"{Color.CYAN}       USERNAME SEARCH MODULE (Enhanced)")
    print(f"{Color.CYAN}{'='*55}\n")
    
    username = input_target("Enter username")
    if not username:
        print_error("Username cannot be empty")
        return

    # Clean username
    username = username.strip().lstrip("@")

    print_info(f"Target Username : {username}")
    print_info(f"Total Sites     : {len(SOCIAL_SITES)}")
    print_info(f"Threads         : {CFG['threads']}")
    print_info("Starting deep scan...\n")

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
                print_success(f"{site_name:<18} → {url}")
                found.append(f"{site_name}: {url}")
            elif status is False:
                print_error(f"{site_name:<18} → Not Found")
                not_found.append(site_name)
            else:
                print_warning(f"{site_name:<18} → Could not determine")
                unknown.append(site_name)

    # Summary
    print(f"\n{Color.CYAN}{'='*55}")
    print(f"{Color.GREEN}[+] Found      : {len(found)} sites")
    print(f"{Color.RED}[-] Not Found  : {len(not_found)} sites")
    print(f"{Color.YELLOW}[!] Unknown    : {len(unknown)} sites")
    print(f"{Color.CYAN}{'='*55}")

    if found:
        print(f"\n{Color.GREEN}Accounts Found:")
        for acc in found:
            print(f"  • {acc}")

    report_data = {
        "Username": username,
        "Total Checked": len(SOCIAL_SITES),
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

# ==================== EMAIL SEARCH (DEEP OSINT) ====================
def email_search():
    print(f"\n{Color.CYAN}{'='*55}")
    print(f"{Color.CYAN}       EMAIL DEEP OSINT MODULE")
    print(f"{Color.CYAN}{'='*55}\n")

    email = input_target("Enter email address")
    if not email or "@" not in email:
        print_error("Invalid email address")
        return

    email = email.strip().lower()
    username, domain = email.split("@", 1)

    print_info(f"Target Email : {email}")
    print_info("Starting deep analysis...\n")

    results = {
        "Email": email,
        "Username": username,
        "Domain": domain
    }
    session = get_session()

    # ========== 1. Basic Validation ==========
    print(f"{Color.MAGENTA}[1] Basic Validation")
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid_format = bool(re.match(email_regex, email))
    results["Valid Format"] = is_valid_format
    print_success(f"Format Valid: {is_valid_format}")

    # Role account detection
    role_keywords = ["admin", "info", "support", "contact", "sales", "help", "noreply", "no-reply", "webmaster", "postmaster", "abuse", "security"]
    is_role = any(username.lower().startswith(k) or username.lower() == k for k in role_keywords)
    results["Is Role Account"] = is_role
    if is_role:
        print_warning("This looks like a Role/Organizational account")
    else:
        print_success("Personal-looking account")

    # ========== 2. Provider Detection ==========
    print(f"\n{Color.MAGENTA}[2] Provider Detection")
    providers = {
        "gmail.com": "Google (Gmail)",
        "googlemail.com": "Google (Gmail)",
        "yahoo.com": "Yahoo",
        "yahoo.co.uk": "Yahoo",
        "outlook.com": "Microsoft (Outlook)",
        "hotmail.com": "Microsoft (Hotmail)",
        "live.com": "Microsoft (Live)",
        "msn.com": "Microsoft",
        "protonmail.com": "ProtonMail",
        "proton.me": "ProtonMail",
        "icloud.com": "Apple (iCloud)",
        "me.com": "Apple",
        "mac.com": "Apple",
        "mail.ru": "Mail.ru",
        "yandex.com": "Yandex",
        "yandex.ru": "Yandex",
        "aol.com": "AOL",
        "zoho.com": "Zoho",
        "gmx.com": "GMX",
        "gmx.net": "GMX",
        "tutanota.com": "Tutanota",
        "fastmail.com": "Fastmail",
    }
    provider = providers.get(domain, "Custom / Self-hosted / Unknown")
    results["Provider"] = provider
    print_success(f"Provider: {provider}")

    # ========== 3. DNS Records (MX, SPF, DMARC) ==========
    print(f"\n{Color.MAGENTA}[3] DNS & Mail Configuration")
    
    # MX
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_list = sorted([(r.preference, str(r.exchange)) for r in mx_records])
        results["MX Records"] = [f"{pref} {ex}" for pref, ex in mx_list]
        print_success(f"MX Records: {results['MX Records']}")
    except Exception as e:
        print_error(f"MX Records: None / Error ({e})")
        results["MX Records"] = "None"

    # SPF
    try:
        txt_records = dns.resolver.resolve(domain, "TXT")
        spf = [str(r) for r in txt_records if "v=spf1" in str(r).lower()]
        results["SPF"] = spf if spf else "Not found"
        if spf:
            print_success(f"SPF: {spf[0][:80]}...")
        else:
            print_warning("SPF: Not found")
    except:
        results["SPF"] = "Error"
        print_warning("SPF: Could not retrieve")

    # DMARC
    try:
        dmarc_records = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        dmarc = [str(r) for r in dmarc_records]
        results["DMARC"] = dmarc if dmarc else "Not found"
        if dmarc:
            print_success(f"DMARC: {dmarc[0][:80]}...")
        else:
            print_warning("DMARC: Not found")
    except:
        results["DMARC"] = "Not found"
        print_warning("DMARC: Not found")

    # ========== 4. Disposable / Temporary Email Check ==========
    print(f"\n{Color.MAGENTA}[4] Disposable Email Check")
    disposable_domains = [
        "tempmail.com", "guerrillamail.com", "10minutemail.com", "mailinator.com",
        "throwaway.email", "yopmail.com", "temp-mail.org", "fakeinbox.com",
        "sharklasers.com", "getnada.com", "maildrop.cc", "dispostable.com",
        "trashmail.com", "mailnesia.com", "tempail.com", "mohmal.com"
    ]
    is_disposable = domain in disposable_domains
    results["Disposable Email"] = is_disposable
    if is_disposable:
        print_error("This is a known Disposable/Temporary email")
    else:
        print_success("Not a known disposable email domain")

    # ========== 5. Gravatar ==========
    print(f"\n{Color.MAGENTA}[5] Gravatar Check")
    import hashlib
    gravatar_hash = hashlib.md5(email.encode()).hexdigest()
    gravatar_url = f"https://www.gravatar.com/avatar/{gravatar_hash}?d=404&s=200"
    gravatar_profile = f"https://www.gravatar.com/{gravatar_hash}"
    try:
        r = session.get(gravatar_url, timeout=8)
        if r.status_code == 200:
            print_success(f"Gravatar EXISTS → {gravatar_profile}")
            results["Gravatar"] = gravatar_profile
            results["Gravatar Image"] = gravatar_url
        else:
            print_error("No Gravatar found")
            results["Gravatar"] = "Not found"
    except Exception as e:
        print_warning(f"Gravatar check failed: {e}")
        results["Gravatar"] = "Error"

    # ========== 6. Domain Whois (for custom domains) ==========
    if domain not in providers:
        print(f"\n{Color.MAGENTA}[6] Domain Whois (Custom Domain)")
        try:
            w = whois.whois(domain)
            domain_info = {
                "Registrar": w.registrar,
                "Creation Date": str(w.creation_date),
                "Expiration Date": str(w.expiration_date),
                "Org": getattr(w, "org", "N/A"),
                "Country": getattr(w, "country", "N/A")
            }
            results["Domain Whois"] = domain_info
            for k, v in domain_info.items():
                print_success(f"{k}: {v}")
        except Exception as e:
            print_warning(f"Whois failed: {e}")
            results["Domain Whois"] = "Failed"

    # ========== 7. Social & Service Registration Hints ==========
    print(f"\n{Color.MAGENTA}[7] Possible Linked Accounts (Public Checks)")
    print_info("Checking public indicators (these do not notify the target)...")

    linked = []

    # Google account indicator (very basic)
    try:
        # Public method - check if Google shows account existence via older endpoints is limited now
        # We use a safe approach
        print_info("Google/Gmail: Manual check recommended via password recovery (do not abuse)")
    except:
        pass

    # Common public profile patterns based on username part
    social_checks = {
        "GitHub": f"https://github.com/{username}",
        "Twitter/X": f"https://x.com/{username}",
        "Instagram": f"https://www.instagram.com/{username}/",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "Keybase": f"https://keybase.io/{username}",
    }

    for service, url in social_checks.items():
        try:
            r = session.get(url, timeout=6, allow_redirects=True)
            content = r.text.lower()
            if r.status_code == 200 and "not found" not in content and "doesn't exist" not in content and "page not found" not in content:
                print_success(f"{service}: Possible account → {url}")
                linked.append(f"{service}: {url}")
            else:
                print_error(f"{service}: No public profile found")
        except:
            print_warning(f"{service}: Check failed")

    results["Possible Linked Profiles"] = linked

    # ========== 8. Additional Info ==========
    print(f"\n{Color.MAGENTA}[8] Summary")
    print_success(f"Email          : {email}")
    print_success(f"Provider       : {provider}")
    print_success(f"Disposable     : {is_disposable}")
    print_success(f"Role Account   : {is_role}")
    print_success(f"Gravatar       : {results.get('Gravatar', 'N/A')}")
    if linked:
        print_success(f"Possible Links : {len(linked)} found")

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
