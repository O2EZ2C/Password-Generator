#!/usr/bin/env python3
"""
memory_key.py

Builds a password from YOUR memories, then trains you to remember it.

Run it:
    python3 memory_key.py

Steps:
  1. Read the instructions
  2. Pick a mode and a difficulty
  3. Answer 5 questions (3 parts)
  4. MEMORISE: the password is shown 3 times and you type it
  5. RECALL: blank screen, type it from memory (hidden)

The password is never written to disk. It only exists while the
script runs.

No extra libraries needed. Standard Python only.
"""

import getpass
import hashlib
import hmac
import secrets
import sys
from datetime import datetime

# ── Settings you can change ─────────────────────────────────────────────
ALLOWED_SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/~"
MIN_WORD_LEN = 3
MAX_WORD_LEN = 15
MEMORISE_ROUNDS = 3

# The three word questions. Edit the wording however you like.
WORD_QUESTIONS = [
    "Q2. Think of a PLACE you remember well.\n"
    "    Type ONE word that reminds you of it: ",
    "Q3. Think of a PERSON, PET or OBJECT from your past.\n"
    "    Type ONE word that reminds you of it: ",
    "Q4. Think of a MOMENT, SONG or FOOD you remember.\n"
    "    Type ONE word that reminds you of it: ",
]


# ── Screen helpers ──────────────────────────────────────────────────────

def clear():
    """Clear the screen AND the scrollback, so the password is not left behind."""
    print("\033[3J\033[2J\033[H", end="", flush=True)


def ask(prompt):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        bye()


def ask_hidden(prompt):
    try:
        return getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt):
        bye()


def yes(prompt):
    return ask(prompt + " (y/n): ").strip().lower().startswith("y")


def bye():
    clear()
    print("Stopped. Nothing was saved.")
    sys.exit(0)


def wait():
    ask("\n[Press Enter to continue] ")


# ── Random sources ──────────────────────────────────────────────────────
# Both have one method: below(n) -> a number from 0 to n-1.

class RandomSource:
    """Different result every run."""

    def below(self, n):
        return secrets.randbelow(n)


class SeededSource:
    """
    Same answers -> same result every time.
    Built on SHA-256 so it does not change between Python versions.
    """

    def __init__(self, seed):
        self.seed = seed
        self.counter = 0
        self.buffer = b""

    def _take(self, count):
        while len(self.buffer) < count:
            block = self.seed + self.counter.to_bytes(8, "big")
            self.buffer += hashlib.sha256(block).digest()
            self.counter += 1
        out, self.buffer = self.buffer[:count], self.buffer[count:]
        return out

    def below(self, n):
        if n <= 1:
            return 0
        limit = (2 ** 32 // n) * n  # avoids bias
        while True:
            value = int.from_bytes(self._take(4), "big")
            if value < limit:
                return value % n


def shuffle(items, rng):
    """Fisher-Yates shuffle using our own random source."""
    for i in range(len(items) - 1, 0, -1):
        j = rng.below(i + 1)
        items[i], items[j] = items[j], items[i]


def split_chunks(text, min_size, max_size, rng):
    """Cut text into pieces of min_size..max_size characters."""
    pieces = []
    pos = 0
    while pos < len(text):
        size = min_size + rng.below(max_size - min_size + 1)
        pieces.append(text[pos:pos + size])
        pos += size
    return pieces


# ── Building the password ───────────────────────────────────────────────

def build_password(words, symbols, number, level, rng):
    """
    Level 1: whole words + symbols + number in groups of 2
    Level 2: words cut into groups of 2-3 letters + symbols
             + number in groups of 1-3 digits
    Level 3: words cut into pieces of 1-3 letters (single letters
             allowed) + symbols + number in groups of 1-3 digits
    Everything is then shuffled together.
    """
    units = []
    for word in words:
        if level == 1:
            units.append(word)
        elif level == 2:
            units += split_chunks(word, 2, 3, rng)
        else:
            units += split_chunks(word, 1, 3, rng)

    units += list(symbols)

    if level == 1:
        units += split_chunks(number, 2, 2, rng)
    else:
        units += split_chunks(number, 1, 3, rng)

    shuffle(units, rng)
    return "".join(units)


def make_seed(words, symbols, number, level):
    material = "|".join([str(level), symbols, *words, number])
    return hashlib.pbkdf2_hmac(
        "sha256", material.encode(), b"memory-key-v1", 200_000
    )


# ── Checking answers ────────────────────────────────────────────────────

def looks_like_date(digits):
    for fmt in ("%d%m%y", "%m%d%y", "%y%m%d"):
        try:
            datetime.strptime(digits, fmt)
            return True
        except ValueError:
            pass
    return False


def looks_predictable(digits):
    if len(set(digits)) == 1:
        return True
    steps = [int(digits[i + 1]) - int(digits[i]) for i in range(len(digits) - 1)]
    return all(s == 1 for s in steps) or all(s == -1 for s in steps)


# ── Screens ─────────────────────────────────────────────────────────────

def show_instructions():
    clear()
    print("=" * 60)
    print("MEMORY KEY  -  password builder")
    print("=" * 60)
    print("""
HOW IT WORKS

1. You answer 5 questions.
   Your answers are the ingredients:
     - 1 or 2 symbols
     - 3 words, each from a real memory
     - 1 six-digit number

2. The program shuffles the ingredients into a password.

3. MEMORISE
   The password is shown 3 times. Each time you type it.

4. RECALL
   The screen goes blank. Type the password from memory.
   Nothing shows as you type.
   Stuck? Type  show  to reveal it, then try again.
   You can only finish once you type it correctly.

TIPS
  - Pick words only YOU would connect to the memory.
  - Pick a number that is NOT a date. Dates are guessable.
  - The password is never saved to disk.
""")
    wait()


def choose_mode():
    clear()
    print("MODE\n")
    print("  1) Random")
    print("     A new password every run. You must remember the")
    print("     result. Your answers can NOT rebuild it.\n")
    print("  2) Repeatable")
    print("     Same answers + same difficulty = same password.")
    print("     You can rebuild it any time by running this again.")
    print("     Your answers become the secret, so choose them well.\n")
    while True:
        choice = ask("Pick 1 or 2: ").strip()
        if choice in ("1", "2"):
            return choice == "2"
        print("Please type 1 or 2.")


def choose_difficulty():
    clear()
    print("DIFFICULTY\n")
    print("  1) Easy    - whole words, symbols and number groups shuffled")
    print("  2) Medium  - words cut into letter groups, then shuffled")
    print("               with symbols and number groups")
    print("  3) Hard    - words cut into single letters and groups,")
    print("               then shuffled with symbols and digits\n")
    while True:
        choice = ask("Pick 1, 2 or 3: ").strip()
        if choice in ("1", "2", "3"):
            return int(choice)
        print("Please type 1, 2 or 3.")


def ask_symbols():
    clear()
    print("PART 1 of 3  -  SYMBOLS\n")
    print("Allowed symbols:  " + " ".join(ALLOWED_SYMBOLS) + "\n")
    while True:
        raw = ask("Q1. Type 1 or 2 symbols (example: !$ ): ")
        symbols = "".join(raw.split())  # remove spaces
        if not 1 <= len(symbols) <= 2:
            print("Please enter 1 or 2 symbols.")
        elif any(ch not in ALLOWED_SYMBOLS for ch in symbols):
            print("One of those is not in the allowed list.")
        elif len(set(symbols)) != len(symbols):
            print("Please use two different symbols.")
        else:
            return symbols


def ask_words():
    clear()
    print("PART 2 of 3  -  WORDS FROM MEMORY\n")
    print(f"Letters only, {MIN_WORD_LEN}-{MAX_WORD_LEN} letters. "
          "Lower case is fine.\n")
    words = []
    for question in WORD_QUESTIONS:
        while True:
            word = ask(question).strip()
            if not word.isalpha():
                print("  Letters only, please (no spaces or numbers).\n")
            elif not MIN_WORD_LEN <= len(word) <= MAX_WORD_LEN:
                print(f"  Use {MIN_WORD_LEN}-{MAX_WORD_LEN} letters.\n")
            elif word.lower() in [w.lower() for w in words]:
                print("  You already used that word. Pick a different one.\n")
            else:
                words.append(word)
                print()
                break
    return words


def ask_number():
    clear()
    print("PART 3 of 3  -  YOUR NUMBER\n")
    print("Q5. Pick a 6 digit number that means something to you.")
    print("    A number NOT linked to any date is statistically stronger.\n")
    while True:
        number = ask("    Six digits: ").strip()
        if not (number.isdigit() and len(number) == 6):
            print("  Please type exactly 6 digits.\n")
            continue
        if looks_predictable(number):
            print("  That is very predictable (repeats or counts up/down).")
            if not yes("  Use it anyway?"):
                continue
        elif looks_like_date(number):
            print("  That could be a date. A number unrelated to any date is stronger.")
            if not yes("  Use it anyway?"):
                continue
        return number


def memorise(password):
    note = ""
    for round_no in range(1, MEMORISE_ROUNDS + 1):
        while True:
            clear()
            print(f"MEMORISE  -  round {round_no} of {MEMORISE_ROUNDS}\n")
            if note:
                print(note + "\n")
            print("Your password:\n")
            print("    " + password + "\n")
            typed = ask("Type it here: ")
            if hmac.compare_digest(typed.encode(), password.encode()):
                note = "Correct."
                break
            note = "Not quite. Look again and retype it."


def recall(password):
    note = ""
    while True:
        clear()
        print("RECALL\n")
        print("Type your password from memory.")
        print("Nothing shows as you type.")
        print("Type  show  to reveal it (you then have to type it again).\n")
        if note:
            print(note + "\n")
        typed = ask_hidden("Password: ")

        if hmac.compare_digest(typed.encode(), password.encode()):
            return
        if typed.strip().lower() == "show":
            clear()
            print("YOUR PASSWORD\n")
            print("    " + password + "\n")
            print("Memorise it, or write it down.")
            wait()
            note = "Now type it again."
        else:
            note = "That was not right. Try again."


def finish(repeatable, level):
    clear()
    print("DONE  -  you typed it correctly from memory.\n")
    if repeatable:
        print("To rebuild this password later, run the program again")
        print("with the SAME mode, difficulty and answers:")
        print(f"  - mode: Repeatable")
        print(f"  - difficulty: {level}")
        print("  - the same symbols, words and number")
    else:
        print("This was Random mode. The password can NOT be rebuilt.")
        print("Make sure you have it memorised, or in a password manager.")
    print("\nNothing was saved to disk.\n")


# ── Main ────────────────────────────────────────────────────────────────

def run_once():
    show_instructions()
    repeatable = choose_mode()
    level = choose_difficulty()

    symbols = ask_symbols()
    words = ask_words()
    number = ask_number()

    if repeatable:
        clear()
        print("Building your password (a few seconds)...")
        rng = SeededSource(make_seed(words, symbols, number, level))
    else:
        rng = RandomSource()

    password = build_password(words, symbols, number, level, rng)

    memorise(password)
    recall(password)
    finish(repeatable, level)


def main():
    while True:
        run_once()
        if not yes("Go back to the start?"):
            break
    clear()
    print("Goodbye. Nothing was saved.")


if __name__ == "__main__":
    main()
