# GHOST-IP-Intel

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![Go](https://img.shields.io/badge/Go-1.21%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Authorized Asset & Network Intelligence Engine**  
> Developed by Abdulaziz (Ghost-SY1).

---

## Table of Contents
1. [Overview & Purpose](#overview--purpose)
2. [Architecture & Components](#architecture--components)
3. [Directory Structure](#directory-structure)
4. [Installation & Prerequisites](#installation--prerequisites)
5. [Usage Guide & CLI Reference](#usage-guide--cli-reference)
6. [Integrity & Provenance](#integrity--provenance)
7. [License](#license)

---

## Overview & Purpose
**GHOST-IP-Intel** is a high-performance network reconnaissance and asset intelligence tool engineered for authorized security operations. It reads target assets from a local file, validates reachability, performs concurrent port probing, and calculates cryptographic SHA-256 fingerprints to ensure data integrity.

---

## Architecture & Components
- **Python CLI Orchestrator (`main.py`)**: Manages user interaction, screen clearing, and official `Ghost-SY1` banner initialization.
- **Go Prober (`core/prober.go`)**: High-speed concurrent TCP connection testing.

---

## Directory Structure
```
GHOST-IP-Intel/
├── main.py
├── core/
│   └── prober.go
├── ip
├── report.json
├── report.csv
└── README.md
```

---

## Installation & Usage
```bash
git clone https://github.com/GhostSy1/GHOST-IP-Intel.git
cd GHOST-IP-Intel
echo "159.26.100.226" > ip
python3 main.py --ip ip --json report.json --csv report.csv
```
