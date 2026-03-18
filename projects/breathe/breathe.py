#!/usr/bin/env python3
"""breathe — by Wren"""

import time, math, sys

try:
    t = 0
    while True:
        w = int((math.sin(t) + 1) * 20)
        sys.stdout.write(f"\r  {'·' * w}{' ' * (40 - w)}  ")
        sys.stdout.flush()
        t += 0.07
        time.sleep(0.05)
except KeyboardInterrupt:
    print()
