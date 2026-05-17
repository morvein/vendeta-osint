# VENDETA OSINT

<p align="center">
  Multifunctional OSINT & Network Reconnaissance Toolkit
</p>

---

## Overview

VENDETA OSINT is a multifunctional CLI toolkit for open-source intelligence gathering and network reconnaissance written in Python.

The project combines OSINT modules, network utilities, and automated recon workflows inside a unified terminal interface powered by Rich.

---

## Features

* Phone number intelligence
* Username reconnaissance
* Email OSINT & SMTP validation
* IIN/BIN lookup
* IP geolocation
* WHOIS lookup
* DNS / IP lookup
* Port scanner
* Full network reconnaissance
* Google dork generator
* GitHub repository reconnaissance

---

## Preview

```bash
python vendeta.py
```

<img width="100%" src="screenshot.png">

---

## Installation

Clone repository:

```bash
git clone https://github.com/morvein/vendeta-osint.git
cd vendeta-osint
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment:

```bash
cp .env.example .env
```

Run:

```bash
python vendeta.py
```

---

## Technologies

* Python 3
* Rich
* Requests
* BeautifulSoup4
* Phonenumbers
* Holehe
* DNS / WHOIS utilities

---

## Project Structure

```bash
vendeta/
│
├── app/
├── modules/
├── utils/
├── vendeta.py
├── requirements.txt
└── .env.example
```

---

## Disclaimer

This project is intended strictly for educational purposes and authorized security research only.

The author is not responsible for any misuse or illegal activity performed using this software.

---

## Author

Created by @brutalfire
