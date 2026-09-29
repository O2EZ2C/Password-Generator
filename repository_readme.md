# Memory Key

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none%20%28standard%20lib%29-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

A lightweight, terminal-based security tool that builds high-entropy passwords from your personal memories, then trains you to recall them using structured memorization routines.

You answer 5 memory-anchored questions. The program fragments and shuffles your answers into a strong password. It then guides you through a two-phase learning process: first visual typing verification, then blind memory recall.

---

## Key Features

- **Zero Dependencies:** Built exclusively using Python standard libraries (`hashlib`, `hmac`, `secrets`, `getpass`). No `pip install` required.
- **In-Memory Execution:** Passwords exist only in active RAM during runtime and are never written to disk or saved to logs.
- **Deterministic or Random Modes:** Generate a fresh, non-reconstructable password, or use deterministic key derivation to rebuild the exact same password anytime using your memory keys.
- **Built-in Recall Training:** Active learning loop forces blind typing to ensure you have successfully memorized the output before closing.

---

## Getting Started

### Prerequisites

- Python 3.8 or higher installed on Linux, macOS, or Windows.

### How to Run

Clone or download the repository, open your terminal in the script directory, and execute:

```bash
python3 memory_key.py
```

*To abort execution at any point, press `Ctrl+C`. The process will clear the terminal and exit without saving any data.*

---

## How It Works

1. **Setup:** Select your operation mode (**Random** or **Repeatable**) and difficulty level (**1, 2, or 3**).
2. **Ingredient Input:** Answer 5 memory questions across 3 parts (Symbols, Words, Number).
3. **Password Generation:** The program fragments your inputs based on difficulty and shuffles them together.
4. **Phase 1 — Memorise:** The password is displayed for 3 rounds. You type it while looking at it to build motor memory.
5. **Phase 2 — Recall:** The screen clears completely. You type the password blind from memory.
6. **Completion:** Execution finishes only when typed correctly from memory.

*Stuck during Recall? Type `show` to temporarily reveal the password, then retry.*

---

## The Input Structure

- **Part 1: Symbols (Q1)** — Enter 1 or 2 distinct allowed symbols (`!@#$%^&*()-_=+[]{};:,.?/~`).
- **Part 2: Words from Memory (Q2–Q4)** — Enter 3 unique words (3–15 letters) associated with a place, a person/pet/object, and a moment/food/song.
- **Part 3: Your Number (Q5)** — Enter a 6-digit number. The program evaluates your choice using built-in heuristics and alerts you if it appears predictable (e.g., `123456`) or date-formatted.

---

## Difficulty Levels

Higher levels increase entropy by breaking your words and numbers into smaller, intermingled sub-chunks before shuffling:

| Level | Word Chunking | Symbol Integration | Number Chunking |
| :--- | :--- | :--- | :--- |
| **1 (Easy)** | Kept whole | Shuffled in | Groups of 2 digits |
| **2 (Medium)** | Cut into 2–3 letter groups | Shuffled in | Groups of 1–3 digits |
| **3 (Hard)** | Cut into 1–3 letter fragments | Shuffled in | Groups of 1–3 digits |

*Example output (Level 1 Easy):* `tigerbiscuit36harbour$1948!`

---

## Security & Architectural Notes

- **Deterministic Key Derivation:** In Repeatable mode, input parameters are hashed using `PBKDF2-HMAC-SHA256` ($200,000$ iterations) with domain separation (`memory-key-v1`) to construct an unbiased deterministic random seed.
- **Side-Channel Mitigation:** String validations during recall use `hmac.compare_digest` to perform constant-time comparisons, eliminating timing-attack vulnerabilities.
- **Unbiased Shuffling:** Custom implementation of the Fisher-Yates shuffle algorithm paired with rejection sampling to eliminate modulo bias during random index selection.
- **Scrollback Buffer Clearing:** Screen transitions issue ANSI escape sequences (`\033[3J\033[2J\033[H`) to clear active screens and attempt terminal scrollback purging.
- **Threat Model Boundary:** Repeatable mode strength is strictly bounded by the unpredictability of your chosen answers. For critical enterprise infrastructure or high-risk accounts, use a dedicated offline password manager.

---

## Customization

You can adjust internal settings or question prompts directly in `memory_key.py`:

```python
# Settings at the top of memory_key.py
ALLOWED_SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/~"
MIN_WORD_LEN = 3
MAX_WORD_LEN = 15
MEMORISE_ROUNDS = 3
```

---

## License

Distributed under the MIT License. See `LICENSE` for details.