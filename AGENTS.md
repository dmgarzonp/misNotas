# AGENTS.md

This file provides guidance to agents and developers when working with code in this repository.

## Project Overview

**Mis Apuntes** is a Premium Quick Notes application for Ubuntu Linux built with Python 3, PyQt6, and SQLite, cloning Apple macOS Sequoia aesthetics and features (frameless rounded window, pastel themes, Math Notes, 4-level typography, checklists, global quick notes, tag organization, password lock).

## Local Skill & Guidelines

Detailed engineering, testing, graphical sudo handling, and design guidelines are defined in `skills/mis-apuntes/SKILL.md`.

## Commands

- **Run application:** `python3 main.py` (or `.venv/bin/python main.py`)
- **Run tests:** `pytest` or `QT_QPA_PLATFORM=offscreen pytest`
- **Format code:** `black .` or `ruff format .`
- **Type checking:** `mypy src/`

## Key Execution Rules

1. **Mandatory Functional Testing:** Every implementation or bugfix must be verified with automated unit tests (`pytest`) and offscreen Qt execution before concluding the task.
2. **Graphical Sudo Dialogs:** If elevated privileges (`sudo`) are required during setup, use graphical authentication prompts (`pkexec` or GUI dialogs).
3. **Apple Minimalist Philosophy:** Clean frameless UI, context menus for advanced actions, 4-level typography, Math Notes, debounced SQLite WAL persistence.
