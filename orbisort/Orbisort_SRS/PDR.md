# Orbisort Product Design Document (PDR) & Software Requirements Specification (SRS)

## 1. Overview
**Orbisort** is an intelligent file organizing application for PC. It watches designated folders (like `Downloads`), automatically categorizes files based on predefined configurations, and securely stores metadata. Most importantly, it features an intelligent assistant that users can interact with (via text or voice) to search, manage, and retrieve their files naturally.

## 2. Objectives
- **Automate File Organization**: Eliminate manual file sorting by watching folders and moving files depending on file extension or content.
- **Provide Intelligent Interaction**: Offer an AI-driven Assistant GUI where users can issue natural language commands (e.g., "Find the invoices from last week", "Organize my Downloads folder now").
- **Search Capabilities**: Fast local search across indexed metadata.
- **Publish & Deploy**: Package the application as a standalone Windows executable.

## 3. Architecture & System Flow
Based on the design goals, Orbisort integrates multiple layers:
1. **Ingestion Layer (Watchdog)**
   - Monitors target directories for new, modified, or moved files.
   - Pushes file paths into a processing pipeline.
2. **Processing Layer (Intelligence)**
   - Resolves file extensions rules.
   - Computes hashes to avoid duplicate files.
   - (Future/Advanced) OCR and document intelligence for deeper classification.
3. **Storage Layer**
   - SQLite Database (`orbisort.db`) tracking paths, hashes, sizes, timestamps, and organization status.
   - Physical File System structuring files under `Organized/<Category>/<Year>/<Month>/<Day>`.
4. **Reasoning & UI Layer**
   - **Main GUI**: A React-like Tkinter interface for managing watcher status, settings, logs, and visualizing organized file counts.
   - **Assistant UI**: A natural language chat widget capable of interpreting commands ("search", "organize", "open").

## 4. Current State Assessment
- Core watcher (`watchdog`) and basic rules engine (via `rules.yaml`) are functional.
- SQLite DB (`db_manager.py`) correctly tracks processed files.
- Modern dark-themed Tkinter GUI (`gui.py`) is partially functional (start/stop works).
- Assistant UI exists but currently relies on basic keyword-matching (`interpreter.py`) rather than true NLP/AI.

## 5. Requirements for Completion (The Path to v1.0)
To "complete" the application according to the initial vision:
1. **Intelligent Command Processing**: Upgrade the `interpreter.py` to use a lightweight LLM/NLP approach to parse arbitrary user intents ("organize", "search", "open").
2. **Integration of Assistant**: The Assistant UI needs to fully connect into the core engines to perform actions.
3. **Packaging**: Generate a standalone `.exe` using PyInstaller to fulfill the "publish" requirement.
