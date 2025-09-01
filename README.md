## WebExtractor
WebExtractor is a powerful **OSINT** and **ethical hacking tool developed in Python**. It is used to extract **email addresses**, **phone numbers**, and **links** (both visible and hidden) from a target website. Designed for cybersecurity professionals, bug bounty hunters, and ethical hackers, it helps gather critical intelligence from web pages.

The extracted links can also assist in identifying potential vulnerabilities in the website, such as SQL injection (SQLi) points, open directories, exposed admin panels, or unvalidated input fields. These links serve as entry points for further vulnerability assessments and exploitation attempts during ethical hacking or penetration testing.

## Features
- **Extracts:**
   - Emails
   - Phone Numbers
   - All Links (visible and hidden)

- Clean and organized output

- Works on Linux and Termux

- Simple CLI interface

- Lightweight and fast
  
## Compatibility
- Linux (Debian, RedHat, Arch, etc.)
- Termux (Android)

The tool automatically detects the environment and installs itself accordingly.

## Disclaimer 
This tool is intended for educational and ethical OSINT purposes only. Use it only on websites you own or have explicit permission to analyze. The developer is not responsible for any misuse of this tool.

 ## Installation
 **Step 1: Clone the Repository**
```bash
git clone https://github.com/s-r-e-e-r-a-j/WebExtractor.git
```
**step2: Navigate to the WebExtractor directory**
```bash
cd WebExtractor
```
**Step 3: Install Dependencies**
```bash
pip3 install -r requirements.txt
```
**Note for Kali, Parrot, Ubuntu 23.04+ users:**

If you see an error like:
```go
error: externally-managed-environment
```
then use:
```bash
pip3 install -r requirements.txt --break-system-packages
```

**Step 4: Run Installer (Linux or Termux)**
```bash
python3 install.py
```
**Then type `y` for install**

**Step 5: Run the Tool**
```bash
webextractor
```

## Usage
**Just run the tool and enter the target URL:**
```bash
webextractor
```
It will display the **extracted emails, phone numbers, and links** in a clean format.

## Uninstallation
**Run the install.py script**
```bash
python3 install.py
```
Then type `n` for uninstall
## License
This project is licensed under the MIT License


