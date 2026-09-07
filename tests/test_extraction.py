#!/usr/bin/env python3
"""
Extraction tests for WebExtractor.

Runs offline against fixed HTML fixtures with known ground truth, so results
are reproducible and no live site is contacted.

    python3 tests/test_extraction.py
"""

import importlib.util
import os
import re
import sys

from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))


def find_tool():
    """Locate webextractor.py whether this file sits in tests/ or at the root."""
    for candidate in (os.path.join(HERE, "webextractor.py"),
                      os.path.join(os.path.dirname(HERE), "webextractor.py")):
        if os.path.exists(candidate):
            return candidate
    raise SystemExit("could not find webextractor.py next to or above this test file")


def load_tool():
    spec = importlib.util.spec_from_file_location("webextractor", find_tool())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


we = load_tool()

BASE = "https://acme.example/"

# A page deliberately loaded with the kinds of numbers that used to be
# reported as phone numbers: CSS percentages, unix timestamps, build
# numbers, order references and image dimensions.
PAGE = """<!DOCTYPE html><html><head><title>Acme</title>
<link rel="stylesheet" href="/wp-content/litespeed/css/c12319ec75db5eafb9.css?ver=7495f">
<style>.hero{padding:16.6666666667% 33.3333333333%;width:1751179046px;flex:1 14.2857142857}
.grid{grid-template-columns:repeat(12,8.3333333333%);max-width:1200px;margin:0 596164}</style>
<script>var build="7.4.95";var ts=1751179046;var ratio=11.1111111111;var px=330867;</script>
</head><body>
<h1>Acme Consulting</h1>
<p>General: <a href="mailto:hello@acme.example?subject=Hi">hello@acme.example</a></p>
<p>Billing: Billing@Acme.Example &nbsp; Careers: careers.team@acme-consulting.co.in</p>
<p>Mobile: +91 98200 12345 &nbsp; Landline: 022-2654 1234 &nbsp; US: +1 (415) 555-0132</p>
<p>UK: +44 20 7946 0958 &nbsp; Toll free: 1800 209 5311 &nbsp;
   <a href="tel:+919820098200">Direct</a></p>
<p>Established 2019. Order ref 20260907001. Invoice 1234567890123456.</p>
<p>Turnover 1,234.56 crore. Score 16.6666666667 out of 100. Period 2019-2026.</p>
<img src="/wp-content/uploads/2026/pepper-commands-300x158.jpg" alt="x">
<a href="/contact">Contact</a> <a href="../about.html">About</a> <a href="team/">Team</a>
<a href="https://twitter.com/acme">Twitter</a>
<a href="https://www.linkedin.com/company/acme">LinkedIn</a>
<a href="https://acme.example/pricing#plans">Pricing</a>
<a href="javascript:void(0)">JS</a> <a href="#top">Top</a>
<form action="/subscribe"></form>
</body></html>"""

EXPECTED_EMAILS = {
    "hello@acme.example",
    "billing@acme.example",
    "careers.team@acme-consulting.co.in",
}

EXPECTED_PHONE_DIGITS = {
    "919820012345", "02226541234", "14155550132",
    "442079460958", "18002095311", "919820098200",
}

EXPECTED_LINKS = {
    "https://acme.example/contact",
    "https://acme.example/about.html",
    "https://acme.example/team/",
    "https://acme.example/subscribe",
    "https://acme.example/pricing",
    "https://acme.example/wp-content/litespeed/css/c12319ec75db5eafb9.css?ver=7495f",
    "https://acme.example/wp-content/uploads/2026/pepper-commands-300x158.jpg",
    "https://twitter.com/acme",
    "https://www.linkedin.com/company/acme",
}

# Real numbers in formats used across several numbering plans.
REAL_NUMBERS = [
    "+91 98200 12345", "+1 (415) 555-0132", "+44 20 7946 0958",
    "+49 30 901820", "+81 3-1234-5678", "04 1234 5678",
    "+91-22-6654-3210", "022-2654 1234", "1800 209 5311",
    "2025550132", "9820012345", "(020) 7946 0958",
    "415-555-0132", "+1 800 555 0199",
]

# Strings that look numeric but are never phone numbers.
NOT_NUMBERS = [
    "1751179046", "20260907001", "16.6666666667", "11.1111111111",
    "14.2857142857", "33.3333333333", "1 33.3333333333", "321575 100",
    "330867 100", "537895 100", "596164 100", "1,234,567.89",
    "192.168.1.100", "2026-09-07", "2019-2026", "978-0-13-235088-4",
    "$1,299.00", "12:30:45", "v1.2.3", "300x158",
    "4111 1111 1111 1111", "1234567890123456", "0000000000",
    "1234567890", "12319ec75db5eafb9", "ver=7495f", "1200px",
]

FAILURES = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    if not condition:
        FAILURES.append(f"{name}: {detail}")
    print(f"  [{status}] {name}" + (f"  -- {detail}" if not condition else ""))


def digits_of(value):
    return re.sub(r"\D", "", value).lstrip("0")


def parse(page):
    soup = BeautifulSoup(page, "html.parser")
    visible = BeautifulSoup(page, "html.parser")
    for tag in visible(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = we.clean_text(visible.get_text(separator=" "))
    return soup, text, we.clean_text(page)


def test_emails():
    print("\nEmails")
    soup, text, html = parse(PAGE)
    found = set(we.scrape_emails(text, html, soup))
    check("all expected addresses found", EXPECTED_EMAILS <= found,
          f"missing {sorted(EXPECTED_EMAILS - found)}")
    check("no false positives", found <= EXPECTED_EMAILS,
          f"unexpected {sorted(found - EXPECTED_EMAILS)}")
    check("case-folded so duplicates collapse", len(found) == 3, f"got {len(found)}")


def test_phones_on_page():
    print("\nPhone numbers (full page)")
    soup, text, _ = parse(PAGE)
    found = we.scrape_phone_numbers(text, soup)
    got = {digits_of(p) for p in found}
    want = {d.lstrip("0") for d in EXPECTED_PHONE_DIGITS}
    check("all real numbers found", want <= got, f"missing {sorted(want - got)}")
    check("no false positives", got <= want, f"unexpected {sorted(got - want)}")


def test_phone_formats():
    print("\nPhone numbers (international formats)")
    for value in REAL_NUMBERS:
        found = we.scrape_phone_numbers(f"Call us on {value} today.")
        ok = any(digits_of(f) == digits_of(value) for f in found)
        check(f"recognises {value}", ok, f"got {found}")


def test_phone_noise():
    print("\nPhone numbers (noise rejection)")
    for value in NOT_NUMBERS:
        found = we.scrape_phone_numbers(f"Value {value} recorded.")
        check(f"rejects {value}", not found, f"returned {found}")


def test_links():
    print("\nLinks")
    soup, _, html = parse(PAGE)
    found = set(we.scrape_links(html, BASE, soup))
    check("relative links resolved", EXPECTED_LINKS <= found,
          f"missing {sorted(EXPECTED_LINKS - found)}")
    check("no javascript: or fragment-only links",
          not any(l.startswith("javascript:") or l.endswith("#top") for l in found))
    check("fragments stripped", "https://acme.example/pricing" in found)
    social = set(we.social_links(sorted(found)))
    check("social links detected", len(social) == 2, f"got {sorted(social)}")


def test_url_normalisation():
    print("\nURL handling")
    check("bare host upgraded to https",
          we.normalize_url("example.com") == "https://example.com")
    check("existing scheme preserved",
          we.normalize_url("http://example.com/a") == "http://example.com/a")
    check("whitespace tolerated",
          we.normalize_url("  example.com  ") == "https://example.com")
    check("junk rejected", we.normalize_url("not a url") is None)
    check("empty rejected", we.normalize_url("") is None)
    check("non-web scheme rejected", we.normalize_url("ftp://example.com") is None)


def main():
    print("WebExtractor extraction tests")
    for test in (test_emails, test_phones_on_page, test_phone_formats,
                 test_phone_noise, test_links, test_url_normalisation):
        test()

    print("\n" + "-" * 60)
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
