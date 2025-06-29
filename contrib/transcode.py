#!/usr/bin/env python3
"""Simple transcoding utility.

This script provides basic interoperability by converting data
between common encodings such as base64 and hexadecimal.

It works on multiple operating systems and requires only Python 3
standard libraries.
"""

import argparse
import base64
import binascii
from pathlib import Path
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert data between common encodings.")
    parser.add_argument(
        "mode",
        choices=["encode", "decode"],
        help="Whether to encode or decode the data.")
    parser.add_argument(
        "--format",
        "-f",
        choices=["base64", "hex"],
        required=True,
        help="Encoding format to use.")
    parser.add_argument(
        "--input",
        "-i",
        help="Input file. Reads from stdin if omitted.")
    parser.add_argument(
        "--output",
        "-o",
        help="Output file. Writes to stdout if omitted.")
    args = parser.parse_args()

    if args.input:
        data = Path(args.input).read_bytes()
    else:
        data = sys.stdin.buffer.read()

    if args.mode == "encode":
        if args.format == "base64":
            out = base64.b64encode(data)
        else:
            out = binascii.hexlify(data)
    else:
        if args.format == "base64":
            out = base64.b64decode(data)
        else:
            # hex decoder expects text
            out = binascii.unhexlify(data.strip())

    if args.output:
        Path(args.output).write_bytes(out)
    else:
        sys.stdout.buffer.write(out)


if __name__ == "__main__":
    main()
