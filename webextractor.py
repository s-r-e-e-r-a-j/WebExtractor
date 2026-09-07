#!/usr/bin/env python3

import re
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
import unicodedata

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
    os.system("cls" if os.name == "nt" else "clear")
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
    # FIX: Timeout/ReadTimeout/TooManyRedirects are NOT subclasses of ConnectionError,
    # so the old code crashed with a traceback on a slow or flaky network.
    except requests.exceptions.RequestException:
        print(f"{Colors.BrightWhite}[{Colors.BrightRed}!{Colors.BrightWhite}] {Colors.BrightRed}No internet connection detected. Try again later.{Colors.Reset}")
        sys.exit(1)


# URL format validation
# FIX: a bare host like "example.com" used to be rejected forever; now it is
# upgraded to https:// instead. Returns the usable URL, or None if unusable.
_HOSTNAME = re.compile(
    r'^(?:'
    r'\[?[0-9A-Fa-f]*:[0-9A-Fa-f:.]*\]?'                    # IPv6 literal
    r'|\d{1,3}(?:\.\d{1,3}){3}'                             # IPv4
    r'|[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?'
    r'(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+'      # dotted hostname
    r')$'
)


def normalize_url(url):
    url = url.strip()
    if not url:
        return None
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.\-]*://', url):
        url = "https://" + url
    try:
        result = urlparse(url)
    except ValueError:
        return None
    if result.scheme not in ("http", "https") or not result.netloc:
        return None
    host = result.hostname or ""
    # reject anything that is not a real hostname or IP -- "not a url" would
    # otherwise sail through as https://not a url
    if host != "localhost" and not _HOSTNAME.match(host):
        return None
    return url


def clean_text(text):
    text = re.sub(r'[​‌‍‎‏﻿]', '', text)
    text = text.replace('․', '.').replace('‧', '.')
    text = unicodedata.normalize("NFKC", text)
    return text


# ---------------------------------------------------------------- emails ----

EMAIL_PATTERN = re.compile(
    r'(?<![A-Z0-9._%+-])[A-Z0-9._%+-]{1,64}@[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?'
    r'(?:\.[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?)*\.[A-Z]{2,24}(?![A-Z0-9-])',
    re.IGNORECASE,
)

BLOCKED_EMAIL_EXT = (
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico',
    '.css', '.js', '.mjs', '.json', '.woff', '.woff2', '.ttf', '.eot',
    '.mp4', '.webm', '.pdf', '.zip', '.map', '.avif',
)


def scrape_emails(text, html, soup=None):
    candidates = set(EMAIL_PATTERN.findall(clean_text(text)))
    candidates |= set(EMAIL_PATTERN.findall(clean_text(html)))

    # FIX: mailto: links are the highest-confidence source of all and were
    # only ever caught by accident. Read them straight off the anchors.
    if soup is not None:
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.lower().startswith('mailto:'):
                addr = href[7:].split('?')[0].strip()
                for found in EMAIL_PATTERN.findall(clean_text(addr)):
                    candidates.add(found)

    emails = set()
    for e in candidates:
        e = e.strip(" .,;:'\"<>()[]").lower()   # FIX: case-fold so Sales@X.com
        if not e or e.count('@') != 1:          # and sales@x.com are one result
            continue
        local, _, domain = e.partition('@')
        if e.endswith(BLOCKED_EMAIL_EXT):
            continue
        if len(domain) > 253 or '..' in e or local.startswith('.') or local.endswith('.'):
            continue
        # a TLD of only digits is a version string or an IP fragment, not a domain
        if domain.rsplit('.', 1)[-1].isdigit():
            continue
        emails.add(e)
    return sorted(emails)


# ---------------------------------------------------------------- phones ----
# FIX: this was the tool's worst bug. The old pattern accepted any run of
# 7+ digits, so CSS percentages (16.6666666667), version strings, order
# references and timestamps all came out labelled "phone number".
#
# The new approach:
#   1. only ever look at VISIBLE text (script/style/noscript stripped),
#   2. require real phone punctuation OR a plain 10-11 digit block,
#   3. refuse to match inside a longer number or a decimal,
#   4. validate the digit count and reject known non-phone shapes.

PHONE_PATTERN = re.compile(r'''
    (?<![\d.,/\w])                      # not glued to a digit, decimal or word
    (?:
        \+\d{1,3}[\s.\-]?               # +91 / +1 / +44 ...
        (?:\(\d{1,5}\)[\s.\-]?)?
        \d{1,5}(?:[\s.\-]\d{2,6}){1,4}
      |
        \(\d{2,5}\)[\s.\-]?             # (022) 2654 1234
        \d{2,6}(?:[\s.\-]\d{2,6}){0,3}
      |
        0\d{1,4}[\s.\-]\d{3,6}(?:[\s.\-]\d{2,6}){0,2}   # 022-2654 1234
      |
        \d{3,5}[\s.\-]\d{3,4}[\s.\-]\d{3,4}             # 415 555 0132
      |
        \d{5}[\s.\-]\d{5}                               # 98200 12345
      |
        \d{3}[\s.\-]\d{4}                               # 555-0132 (local)
      |
        (?<!\d)\d{10,11}(?!\d)                          # bare 10-11 digit run
    )
    (?![\d.,]*\d)                       # nothing numeric may follow
''', re.VERBOSE)

# shapes that are digits but are never phone numbers
_YEAR_RANGE = re.compile(r'^(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}$')
# YYYYMMDD... timestamps and date-stamped order references
_DATESTAMP = re.compile(r'^(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])')


def _plausible_phone(raw):
    digits = re.sub(r'\D', '', raw)
    n = len(digits)

    if n < 7 or n > 15:                       # ITU E.164 allows at most 15
        return False
    if _YEAR_RANGE.match(raw.strip()):
        return False
    if len(set(digits)) <= 1:                 # 0000000, 1111111111
        return False
    if digits.startswith('0' * 4):
        return False
    # a bare digit run with no punctuation is only credible at national length,
    # and must not be a YYYYMMDD-style timestamp or order reference
    if not re.search(r'[\s.\-()+]', raw.strip()):
        if n not in (10, 11):
            return False
        if _DATESTAMP.match(digits):
            return False
        # no national numbering plan starts a 10-digit subscriber number with
        # 0 or 1 -- those are unix timestamps, ids and counters
        if n == 10 and digits[0] in '01':
            return False
    # sequential runs like 1234567890 / 0123456789 are test data, not numbers
    if digits in '01234567890123456789' or digits in '09876543210987654321':
        return False
    return True


def _tidy_phone(raw):
    return re.sub(r'\s{2,}', ' ', raw.strip(" .,;:-–"))


# Payment-card numbers are written as 4-digit groups and would otherwise be
# harvested as phone numbers. Blank them out before scanning, so they are
# neither reported nor written to disk.
_CARD_LIKE = re.compile(r'(?<!\d)(?:\d{4}[\s\-]){3,4}\d{1,4}(?!\d)')


def _mask_card_numbers(text):
    return _CARD_LIKE.sub(lambda m: ' ' * len(m.group()), text)


def scrape_phone_numbers(text, soup=None):
    found = {}

    # FIX: tel: links are unambiguous. Take them first and always keep them.
    if soup is not None:
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.lower().startswith('tel:'):
                num = _tidy_phone(href[4:].split('?')[0])
                digits = re.sub(r'\D', '', num)
                if 7 <= len(digits) <= 15:
                    found[digits.lstrip('0')] = num

    for match in PHONE_PATTERN.finditer(_mask_card_numbers(clean_text(text))):
        raw = _tidy_phone(match.group())
        if not _plausible_phone(raw):
            continue
        key = re.sub(r'\D', '', raw).lstrip('0')
        # keep the best-formatted version of each distinct number
        if key not in found or len(raw) > len(found[key]):
            found[key] = raw

    return sorted(found.values())


# ----------------------------------------------------------------- links ----
# FIX: the old version only saw absolute http(s) URLs sitting in the raw HTML,
# so every relative link (/contact, ../about.html) was silently dropped.

LINK_ATTRS = (('a', 'href'), ('link', 'href'), ('area', 'href'),
              ('script', 'src'), ('img', 'src'), ('iframe', 'src'),
              ('source', 'src'), ('video', 'src'), ('audio', 'src'),
              ('embed', 'src'), ('form', 'action'))

RAW_LINK_PATTERN = re.compile(r'https?://[^\s"\'<>\\)]+', re.IGNORECASE)

SOCIAL_HOSTS = ('facebook.com', 'twitter.com', 'x.com', 'instagram.com',
                'linkedin.com', 'youtube.com', 'youtu.be', 't.me', 'wa.me',
                'github.com', 'pinterest.com', 'reddit.com', 'tiktok.com',
                'threads.net', 'mastodon.social', 'discord.gg')


def scrape_links(html, base_url=None, soup=None):
    links = set()

    if soup is not None:
        base = base_url
        base_tag = soup.find('base', href=True)
        if base_tag and base_url:
            base = urljoin(base_url, base_tag['href'])
        for tag_name, attr in LINK_ATTRS:
            for tag in soup.find_all(tag_name):
                value = (tag.get(attr) or '').strip()
                if not value:
                    continue
                low = value.lower()
                if low.startswith(('mailto:', 'tel:', 'javascript:', 'data:', '#')):
                    continue
                absolute = urljoin(base, value) if base else value
                absolute, _ = urldefrag(absolute)
                if absolute.lower().startswith(('http://', 'https://')):
                    links.add(absolute)

    for found in RAW_LINK_PATTERN.findall(html):
        links.add(urldefrag(found.rstrip('.,;:)\'"'))[0])

    return sorted(links)


def social_links(links):
    return [l for l in links if any(h in urlparse(l).netloc.lower() for h in SOCIAL_HOSTS)]


# ------------------------------------------------------------------ main ----

def scrape_website(url, scrape_em, scrape_ph, scrape_ln):
    try:
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/124.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        res = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        res.raise_for_status()

        # FIX: without this, pages that do not declare a charset came back as
        # mojibake and their text was unsearchable.
        if not res.encoding or res.encoding.lower() == 'iso-8859-1':
            res.encoding = res.apparent_encoding or 'utf-8'

        ctype = res.headers.get('Content-Type', '')
        if 'html' not in ctype.lower() and 'xml' not in ctype.lower() and ctype:
            print(f"{Colors.BrightYellow}[!] Warning: server returned '{ctype}', not HTML.{Colors.Reset}")

        soup = BeautifulSoup(res.text, 'html.parser')

        # FIX: strip code before reading visible text, so script and CSS
        # numbers can never be mistaken for phone numbers.
        visible = BeautifulSoup(res.text, 'html.parser')
        for bad in visible(['script', 'style', 'noscript', 'template']):
            bad.decompose()
        text = clean_text(visible.get_text(separator=' '))
        html = clean_text(res.text)
        results = {}

        if scrape_em:
            emails = scrape_emails(text, html, soup)
            results['emails'] = emails
            print(f"\n{Colors.BrightYellow}[+] Emails Found ({len(emails)}):{Colors.Reset}")
            print("\n".join(emails) if emails else "None")

        if scrape_ph:
            phones = scrape_phone_numbers(text, soup)
            results['phones'] = phones
            print(f"\n{Colors.BrightYellow}[+] Phone Numbers Found ({len(phones)}):{Colors.Reset}")
            print("\n".join(phones) if phones else "None")

        if scrape_ln:
            links = scrape_links(html, res.url, soup)
            results['links'] = links
            print(f"\n{Colors.BrightYellow}[+] Links Found ({len(links)}):{Colors.Reset}")
            print("\n".join(links) if links else "None")

            socials = social_links(links)
            if socials:
                results['social'] = socials
                print(f"\n{Colors.BrightYellow}[+] Social Links ({len(socials)}):{Colors.Reset}")
                print("\n".join(socials))

        if not res.text.strip() or len(text.strip()) < 40:
            print(f"\n{Colors.BrightYellow}[!] This page carries almost no static text. "
                  f"It is probably rendered by JavaScript, which this tool does not run, "
                  f"so results may be empty.{Colors.Reset}")

        return results

    except requests.exceptions.RequestException as err:
        print(f"{Colors.BrightRed}[!] Error: {err}{Colors.Reset}")
        return {}


def save_results(results, folder):
    try:
        os.makedirs(folder, exist_ok=True)
        written = []
        for key, filename in (('emails', 'emails.txt'), ('phones', 'phones.txt'),
                              ('links', 'links.txt'), ('social', 'social_links.txt')):
            if results.get(key):
                path = os.path.join(folder, filename)
                # FIX: explicit utf-8, or non-ASCII data crashed the save on
                # systems with a non-UTF-8 default locale.
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(results[key]) + "\n")
                written.append(filename)
        if written:
            print(f"{Colors.BrightGreen}[+] Saved {', '.join(written)} in '{folder}'{Colors.Reset}")
        else:
            print(f"{Colors.BrightYellow}[!] Nothing to save.{Colors.Reset}")
    except OSError as e:
        print(f"{Colors.BrightRed}[!] Failed to save results: {e}{Colors.Reset}")


def main():
    display_banner()
    check_connection()

    while True:
        raw = input(f"{Colors.BrightGreen}[+] Enter a valid URL: {Colors.Reset}")
        url = normalize_url(raw)
        if url:
            if url != raw.strip():
                print(f"{Colors.BrightYellow}[*] Using {url}{Colors.Reset}")
            break
        print(f"{Colors.BrightRed}[!] Invalid URL. Try again.{Colors.Reset}")

    scrape_em = input(f"{Colors.BrightYellow}[?] Scrape emails? (y/n): {Colors.Reset}").strip().lower().startswith('y')
    scrape_ph = input(f"{Colors.BrightYellow}[?] Scrape phone numbers? (y/n): {Colors.Reset}").strip().lower().startswith('y')
    scrape_ln = input(f"{Colors.BrightYellow}[?] Scrape links? (y/n): {Colors.Reset}").strip().lower().startswith('y')

    if not any([scrape_em, scrape_ph, scrape_ln]):
        print(f"{Colors.BrightRed}[!] No options selected. Exiting...{Colors.Reset}")
        sys.exit(0)

    results = scrape_website(url, scrape_em, scrape_ph, scrape_ln)

    if any(results.values()):
        if input(f"\n{Colors.BrightGreen}[?] Save results to folder? (y/n): {Colors.Reset}").strip().lower().startswith('y'):
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
        print(f"\n{Colors.BrightRed}[!] User aborted.{Colors.Reset}")
        sys.exit(130)
    except EOFError:
        # FIX: piping input or pressing Ctrl-D used to dump a raw traceback.
        print(f"\n{Colors.BrightRed}[!] Input stream closed.{Colors.Reset}")
        sys.exit(1)
