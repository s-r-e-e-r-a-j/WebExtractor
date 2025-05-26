#!/usr/bin/env python3

import re
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Terminal color codes
class Colors:
    BrightRed = "\033[1;91m"
    BrightGreen = "\033[1;92m"
    BrightYellow = "\033[1;93m"
    BrightWhite = "\033[1;97m"
    Cyan = "\033[1;96m"
    Reset = "\033[0m"

# Display tool banner
def display_banner():
    os.system("clear")
    print(f"{Colors.BrightGreen}")
    print(r"""
      __          __  _     ______      _                  _             
      \ \        / / | |   |  ____|    | |                | |            
       \ \  /\  / /__| |__ | |__  __  _| |_ _ __ __ _  ___| |_ ___  _ __ 
        \ \/  \/ / _ \ '_ \|  __| \ \/ / __| '__/ _` |/ __| __/ _ \| '__|
         \  /\  /  __/ |_) | |____ >  <| |_| | | (_| | (__| || (_) | |   
          \/  \/ \___|_.__/|______/_/\_\\__|_|  \__,_|\___|\__\___/|_|   
                                                                    
                                                  Developer: Sreeraj         
                                                                  
                          """)
    print(f"{Colors.Cyan}* Email, Phone Number, and Link Scraper Tool {Colors.Reset}")
    print(f"{Colors.BrightYellow}* GitHub: https://github.com/s-r-e-e-r-a-j{Colors.Reset}\n")
  
# Check internet connectivity
def check_connection():
    print(f"{Colors.BrightWhite}[{Colors.BrightRed}!{Colors.BrightWhite}] {Colors.BrightRed}Checking internet connection...{Colors.Reset}")
    try:
        requests.get("http://google.com", timeout=10)
        print(f"{Colors.BrightWhite}[{Colors.BrightYellow}*{Colors.BrightWhite}] {Colors.BrightYellow}Connected to the internet.{Colors.Reset}")
    except requests.ConnectionError:
        print(f"{Colors.BrightWhite}[{Colors.BrightRed}!{Colors.BrightWhite}] {Colors.BrightRed}No internet connection detected. Try again later.{Colors.Reset}")
        sys.exit(1)

# URL format validation
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# Email extraction using regex
def scrape_emails(text):
    email_pattern = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.IGNORECASE)
    return list(set(email_pattern.findall(text)))

#  phone number extraction 
def scrape_phone_numbers(text):
    phone_pattern = re.compile(r'(\+?\d{1,3})?[\s\-\.]?\(?\d{2,4}\)?[\s\-\.]?\d{3,5}[\s\-\.]?\d{3,5}')
    phone_numbers = [match.group().strip() for match in re.finditer(phone_pattern, text) if len(match.group().strip()) >= 7]
    return list(set(phone_numbers))  # Remove duplicates

# Link extraction using regex (liks with and without query parameters)
def scrape_links(text):
    link_pattern = re.compile(r'https?://[^\s"\']+', re.IGNORECASE)
    return list(set(link_pattern.findall(text)))

# Main scraping logic
def scrape_website(url, scrape_em, scrape_ph, scrape_ln):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        html = res.text
        results = {}

        if scrape_em:
            emails = scrape_emails(text)
            results['emails'] = emails
            print(f"\n{Colors.BrightYellow}[+] Emails Found:{Colors.Reset}")
            print("\n".join(emails) if emails else "None")

        if scrape_ph:
            phones = scrape_phone_numbers(text)
            results['phones'] = phones
            print(f"\n{Colors.BrightYellow}[+] Phone Numbers Found:{Colors.Reset}")
            print("\n".join(phones) if phones else "None")

        if scrape_ln:
            links = scrape_links(html)
            results['links'] = links
            print(f"\n{Colors.BrightYellow}[+] Links Found:{Colors.Reset}")
            print("\n".join(links) if links else "None")

        return results

    except requests.exceptions.RequestException as err:
        print(f"{Colors.BrightRed}[!] Error: {err}{Colors.Reset}")
        return {}

# Save extracted results
def save_results(results, folder):
    try:
        os.makedirs(folder, exist_ok=True)
        if results.get('emails'):
            with open(os.path.join(folder, 'emails.txt'), 'w') as f:
                f.write("\n".join(results['emails']))
        if results.get('phones'):
            with open(os.path.join(folder, 'phones.txt'), 'w') as f:
                f.write("\n".join(results['phones']))
        if results.get('links'):
            with open(os.path.join(folder, 'links.txt'), 'w') as f:
                f.write("\n".join(results['links']))
        print(f"{Colors.BrightGreen}[+] Results saved in '{folder}'{Colors.Reset}")
    except Exception as e:
        print(f"{Colors.BrightRed}[!] Failed to save results: {e}{Colors.Reset}")

# Main function with user interaction
def main():
    display_banner()
    check_connection()

    while True:
        url = input(f"{Colors.BrightGreen}[+] Enter a valid URL: {Colors.Reset}").strip()
        if is_valid_url(url):
            break
        print(f"{Colors.BrightRed}[!] Invalid URL. Try again.{Colors.Reset}")

    scrape_em = input(f"{Colors.BrightYellow}[?] Scrape emails? (y/n): {Colors.Reset}").lower() == 'y'
    scrape_ph = input(f"{Colors.BrightYellow}[?] Scrape phone numbers? (y/n): {Colors.Reset}").lower() == 'y'
    scrape_ln = input(f"{Colors.BrightYellow}[?] Scrape links? (y/n): {Colors.Reset}").lower() == 'y'

    if not any([scrape_em, scrape_ph, scrape_ln]):
        print(f"{Colors.BrightRed}[!] No options selected. Exiting...{Colors.Reset}")
        sys.exit(0)

    results = scrape_website(url, scrape_em, scrape_ph, scrape_ln)

    if any(results.values()):
        if input(f"{Colors.BrightGreen}[?] Save results to folder? (y/n): {Colors.Reset}").lower() == 'y':
            while True:
                folder = input(f"{Colors.BrightGreen}[+] Enter folder name: {Colors.Reset}").strip()
                if folder:
                    save_results(results, folder)
                    break
                print(f"{Colors.BrightRed}[!] Folder name cannot be empty.{Colors.Reset}")

    print(f"{Colors.BrightRed}[*] Exiting...{Colors.Reset}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
            print(f"{Colors.BrightRed} User Aborted {Colors.Reset}");
            sys.exit()
