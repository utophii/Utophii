#!/usr/bin/env python3

import hashlib
import re
from pathlib import Path

README = Path(__file__).parent / "README.md"
SVG = Path(__file__).parent / "profile.svg"


def main():
    token = hashlib.sha1(SVG.read_bytes()).hexdigest()[:8]
    text = README.read_text(encoding="utf-8")
    new = re.sub(r"profile\.svg\?v=[0-9a-f]+", f"profile.svg?v={token}", text)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print(f"README bumped to ?v={token}")
    else:
        print("README already fresh")


if __name__ == "__main__":
    main()
