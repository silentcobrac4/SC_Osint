# 🔍 SC Osint

**SC Osint** is a powerful Open Source Intelligence (OSINT) tool written in Python.  
It allows you to gather information about usernames, phone numbers, domains, IP addresses, emails, and more using publicly available sources.

> **Educational & Research purposes only.**  
> The author is not responsible for any misuse of this tool.

---

## ✨ Features

- 🔎 **Username Search** — Check username availability across 25+ social platforms
- 📞 **Phone Number Analysis** — Carrier, region, timezone, and validation
- 🌐 **Website / Domain / IP Lookup** — Whois, DNS records, HTTP headers
- 📧 **Email Investigation** — MX records, provider detection, Gravatar check
- 🕵️‍♂️ **Google Dorks Generator** — Ready-to-use advanced search queries
- 🚪 **Port Scanner** — Quick, full, or custom port scanning
- 🛡️ **Proxy Support** — Route requests through HTTP/SOCKS proxies
- 📄 **Automatic Reports** — Results saved automatically in `Reports/` folder
- 🎨 **Colored Interface** — Clean and modern terminal UI

---

## 📦 Installation

### Requirements
- Python 3.8 or higher
- pip

### Steps

```bash
# Clone or download the tool
cd SC_Osint

# Install dependencies
pip install -r requirements.txt

# Run the tool
python3 SC_Osint.py
```

---

## ⚙️ Configuration

Edit the `config.ini` file to customize settings:

```ini
[SETTINGS]
proxy =                  # Example: http://127.0.0.1:8080
timeout = 10
threads = 15
auto_save = True
reports_folder = Reports

[API]
whoisxml_api =           # Optional
hunter_api =             # Optional
numverify_api =          # Optional
```

---

## 🚀 Usage

After running the tool, you will see the main menu:

```
[1]  Username Search
[2]  Phone Number Search
[3]  Website / Domain / IP
[4]  Email Search
[5]  Google Dorks
[6]  Port Scanner
[7]  Proxy / IP Info
[8]  About
[0]  Exit
```

Just select the number of the module you want to use.

---

## 📁 Project Structure

```
SC_Osint/
├── SC_Osint.py          # Main tool
├── config.ini           # Configuration file
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── Reports/             # Auto-generated reports (created on first run)
```

---

## ⚠️ Disclaimer

This tool is intended **only for educational and legitimate research purposes**.  
Unauthorized scanning, data collection, or any illegal activity is strictly prohibited.  
Use it responsibly and at your own risk.

---

## 📜 License

This project is open source.  
Feel free to modify and distribute it under your own name.

---

**Made with ❤️ | SC Osint v1.0**
