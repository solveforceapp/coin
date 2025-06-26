#!/usr/bin/env python3
"""Calculate a simple 'energy' score for given words.

Usage:
    word_energy.py WORD [WORD ...]

The energy of a word is defined as the sum of the squares of each
letter's position in the English alphabet (A=1, B=2, ... Z=26).
Non-alphabetic characters are ignored.
"""

from __future__ import annotations

import argparse
import string

ALPHABET = {letter: idx + 1 for idx, letter in enumerate(string.ascii_lowercase)}


def word_energy(word: str) -> int:
    """Return the 'energy' of ``word``."""
    total = 0
    for char in word.lower():
        value = ALPHABET.get(char)
        if value is not None:
            total += value * value
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute the energy of words")
    parser.add_argument("words", nargs="+", help="Words to analyze")
    args = parser.parse_args()

    for word in args.words:
        print(f"{word}: {word_energy(word)}")


if __name__ == "__main__":
    main()
