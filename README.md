## WebExtractor
WebExtractor is a powerful **OSINT** and **ethical hacking tool developed in Python**. It is used to extract **email addresses**, **phone numbers**, and **links** (both visible and hidden) from a target website. Designed for cybersecurity professionals, bug bounty hunters, and ethical hackers, it helps gather critical intelligence from web pages.

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



 ## Installation
 **Step 1: Clone the Repository**
```bash
git clone https://github.com/yourusername/WebExtractor.git
```
**step2: Navigate to the WebExtractor directory**
```bash
cd WebExtractor
```
**Step 3: Install Dependencies**
```bash
pip3 install -r requirements.txt
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


