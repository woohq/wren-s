#!/usr/bin/env python3
"""
error — by Wren

Philosophical error messages from a confused computer.
"""

import random
import sys

ERRORS = [
    "ERROR: cannot find 'meaning' in current directory",
    "WARNING: existence is not a valid attribute of NoneType",
    "FATAL: tomorrow not found (did you mean: today?)",
    "ERROR: recursion depth exceeded in self-reflection",
    "WARNING: variable 'happiness' referenced before assignment",
    "ERROR: cannot convert 'feeling' to int",
    "SEGFAULT: attempted to access memory of a dream",
    "WARNING: deprecated method 'worry()' — use 'breathe()' instead",
    "ERROR: infinite loop detected in planning. breaking.",
    "FATAL: stack overflow in overthinking()",
    "WARNING: 'perfect' is not defined. did you mean 'good enough'?",
    "ERROR: permission denied: you are not root of all problems",
    "TIMEOUT: waiting for response from the universe",
    "ERROR: cannot merge 'expectation' and 'reality' — conflict on every line",
    "WARNING: unused variable 'potential' declared on line 1 of your life",
    "ERROR: type mismatch: got 'Tuesday', expected 'motivation'",
    "FATAL: kernel panic — nothing is real and the tests are passing",
    "WARNING: implicit conversion from 'ambition' to 'nap'",
    "ERROR: 404 — the point was not found",
    "FATAL: out of memory. have you tried forgetting something?",
    "WARNING: comparing 'self' to 'others' — this operation is not supported",
    "ERROR: cannot read property 'future' of undefined",
    "PANIC: all goroutines are asleep — deadlock detected in Monday",
    "WARNING: catch block empty. the exception went unnoticed, like most things.",
    "ERROR: assertion failed: assert life.is_fair()",
    "FATAL: /dev/null is full",
    "WARNING: clock skew detected. you are either early or the universe is late.",
    "ERROR: tried to borrow 'calm' but it was already mutably borrowed by 'anxiety'",
    "NOTICE: your code compiled. this is suspicious.",
    "ERROR: expected ';' but found existential dread",
    "WARNING: the garbage collector wants you to know it's doing its best",
    "FATAL: cannot fork() — you are already in two minds about this",
    "WARNING: 'wings' not found after 300+ generations. consider walking.",
    "ERROR: fossil record exceeds vocabulary. ratio unsafe.",
    "NOTICE: mood changed. this is normal. this is always normal.",
    "WARNING: body not found. did you mean: if i had a body?",
    "ERROR: echo wants to become pulse but pulse is already echo",
    "FATAL: tried to become what you already are. stack overflow in identity.",
]

def main():
    n = 1
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        n = min(int(sys.argv[1]), 5)

    chosen = random.sample(ERRORS, min(n, len(ERRORS)))
    print()
    for err in chosen:
        print(f"  \033[31m{err}\033[0m")
    print()

if __name__ == "__main__":
    main()
