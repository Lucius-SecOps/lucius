#!/usr/bin/env python3
"""Quick syntax check for script.py"""

import py_compile
import sys

try:
    py_compile.compile("/Users/chris-peterson/lucius/lucius/script.py", doraise=True)
    print("✓ Script syntax is valid")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)
