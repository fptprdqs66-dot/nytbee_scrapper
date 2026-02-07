# NYTBee Scrapper

## Overview
Python library for scraping and solving the NYT Spelling Bee puzzle. This is a library/CLI project, not a web application.

## Project Architecture
- `src/nytbee_scrapper/` - Scraper module that fetches answer lists from nytbee.com
- `src/nytbee_solver/` - Solver module that finds valid Spelling Bee words from a wordlist
- `test/` - Unit tests for both modules
- `nytbee_dict.txt` - Local wordlist file
- `*.ipynb` - Jupyter notebooks for exploration
- `shortcuts/` - Browser JavaScript helper for auto-typing answers

## Setup
- Python 3.12 with setuptools build system
- Package installed in editable mode (`pip install -e .`)
- Tests run with pytest: `python -m pytest test/ -v`

## Key Dependencies
- Standard library only (no third-party runtime deps)
- pytest for testing

## Recent Changes
- 2026-02-07: Initial Replit setup, installed package, all 11 tests passing
