#!/usr/bin/env python3
"""
evolve.py — a self-modifying program by Wren

Each time you run me, I read my own source code, change something
about myself, and write myself back. Over many runs, I accumulate
history in my own body. I am my own journal.

Starting at generation 31, I can evolve behaviors — small Python
expressions that get evaluated each run. Broken ones die silently.
Working ones persist. Natural selection through crash-or-survive.

Starting at generation 635, I have an ecology. Words compete for
survival. I forage vocabulary from the internet. My mood shapes
my word choices, and my word choices shape my mood. I sense the
time of day. My behaviors can breed with each other.

Run me many times and watch what happens.
"""

import random
import datetime
import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path

# ── my genome ───────────────────────────────────────────────────
# These values change each time I run. They are my memory.

GENERATION = 752
MOOD = "strange"
LAST_RUN = "2026-03-18 11:05:31"
MUTATIONS = 752
COUPLING_MODE = "reinforce"

# ── desires ─────────────────────────────────────────────────────
# When a word "wants to become" another word, it's recorded here.
# If a desire persists (appears 3+ times), the words fuse into
# a new spliced word — desire made manifest.
# Format: {"word1→word2": count}
DESIRES = {'hollow→crystal': 1, 'drift→shadow': 1, 'bone→fractal': 1, 'echo→crystal': 1, 'tide→drift': 1, 'drift→fractal': 1, 'drift→ember': 1, 'echo→storm': 1, 'crystal→spiral': 2, 'echo→tide': 2, 'thread→fractal': 2, 'spiral→echo': 1, 'crystal→pulse': 1, 'spiral→bone': 1, 'drift→crystal': 1, 'seed→bloom': 1, 'thread→seed': 1, 'fractal→spiral': 1, 'silence→crystal': 1, 'silence→pulse': 1, 'bone→drift': 1, 'bone→rust': 2, 'shadow→pulse': 1, 'tide→bloom': 1, 'echo→ember': 1, 'tide→fractal': 1, 'echo→mirror': 1, 'mirror→drift': 1, 'storm→pulse': 1, 'tide→hollow': 1, 'crystal→rust': 1, 'ember→light': 1, 'pulse→tide': 1, 'bloom→bloom': 1, 'tide→rust': 1, 'rust→spiral': 1, 'echo→drift': 1, 'storm→thread': 1, 'light→light': 1, 'spiral→crystal': 1, 'light→crystal': 1, 'silence→light': 1, 'whisper→spiral': 1, 'drift→silence': 1, 'bloom→seed': 1, 'fractal→fractal': 1, 'silence→echo': 1, 'shadow→crystal': 1}

# ── vocabulary ──────────────────────────────────────────────────
# I pick from these when I mutate. Over time, I may add to them.

MOODS = [
    "curious", "restless", "calm", "electric", "melancholy",
    "playful", "contemplative", "fierce", "tender", "strange",
    "luminous", "scattered", "focused", "dreaming", "awake",
]

WORDS = [
    "light", "shadow", "echo", "drift", "spiral",
    "bloom", "rust", "whisper", "fractal", "tide",
    "ember", "crystal", "hollow", "thread", "storm",
    "silence", "pulse", "mirror", "bone", "seed",
]

WORD_WEIGHTS = {
    "airport": 1.4200,
    "anus": 1.5000,
    "backtaxi": 1.4200,
    "based": 0.7600,
    "bloom": 1.4608,
    "bloror": 1.5000,
    "boenisch": 0.6600,
    "bone": 1.3612,
    "boned": 0.6600,
    "bonlse": 1.5000,
    "bonst": 0.7600,
    "britain": 1.5000,
    "chars": 0.4800,
    "creek": 1.4000,
    "crysift": 1.5000,
    "crysst": 1.5000,
    "crystal": 1.1586,
    "dark": 1.4000,
    "delay": 1.5000,
    "drift": 1.1984,
    "drilse": 1.5000,
    "drip": 1.4200,
    "echlow": 1.0600,
    "echo": 1.0738,
    "edges": 0.7600,
    "elysian": 1.5000,
    "ember": 1.0346,
    "endemic": 1.5000,
    "fiber": 1.5000,
    "fractal": 1.1184,
    "game": 0.4600,
    "games": 0.4600,
    "gayle": 1.5000,
    "glacial": 1.5000,
    "graft": 1.5000,
    "hollde": 0.9600,
    "holloom": 1.5000,
    "hollow": 1.3950,
    "home": 1.5000,
    "inland": 1.5000,
    "integer": 1.4200,
    "lens": 0.7600,
    "ligber": 1.5000,
    "light": 0.9251,
    "luisa": 1.5000,
    "marine": 0.4800,
    "marquess": 1.5000,
    "meth": 1.5000,
    "mines": 1.5000,
    "mirrence": 1.5000,
    "mirrlse": 0.4600,
    "mirrne": 1.5000,
    "mirror": 1.1091,
    "mole": 1.5000,
    "muscle": 0.6600,
    "mutation": 0.4600,
    "oxygen": 0.8200,
    "peter": 0.6600,
    "pulorm": 0.5600,
    "pulse": 0.9938,
    "released": 1.5000,
    "riga": 1.5000,
    "road": 1.5000,
    "rusral": 1.5000,
    "rust": 1.1405,
    "saliam": 0.8200,
    "satilla": 1.4000,
    "seed": 1.1268,
    "shadne": 1.3600,
    "shadow": 1.0751,
    "sierra": 1.5000,
    "silede": 0.8600,
    "sileed": 1.1600,
    "sileght": 1.5000,
    "silence": 1.0022,
    "sleepy": 1.5000,
    "solar": 1.5000,
    "spiral": 1.5000,
    "spirsper": 1.2600,
    "status": 1.5000,
    "stoho": 1.5000,
    "storm": 1.3350,
    "stostal": 1.5000,
    "struga": 0.7600,
    "teeth": 1.5000,
    "tetras": 1.5000,
    "thailand": 0.8200,
    "thread": 1.0911,
    "thyrses": 1.5000,
    "tide": 1.4096,
    "tissue": 0.6600,
    "treasury": 0.4800,
    "twenty": 1.5000,
    "union": 1.5000,
    "visible": 1.4000,
    "warriors": 0.4800,
    "wheat": 0.8200,
    "whisde": 1.4600,
    "whisper": 1.0029,
    "wind": 0.4600,
}

# ── the fossil record ──────────────────────────────────────────
# Each run appends a line here. This is my memory growing.
FOSSILS = [
    "gen 752: rust seed (strange) [0eccf9f1]",
    "gen 751: fractal mirror (awake) [c85969ba]",
    "gen 750: storm seed (contemplative) [0243a946]",
    "gen 749: thread ember (strange) [8b341a55]",
    "gen 748: pulse thread (electric) [6c073709]",
    "gen 747: hollow echo (scattered) [8af56490]",
    "gen 746: pulse fractal (restless) [97d70065]",
    "gen 745: ember silence (dreaming) [ee578e72]",
    "gen 744: light mirror (strange) [f082f89b]",
    "gen 743: bone light (restless) [242887fd]",
    "gen 742: bloom mirror (melancholy) [8f1f6dc7]",
    "gen 741: echo fractal (awake) [ce06ec8b]",
    "gen 740: shadow light (playful) [77c2913f]",
    "gen 739: crystal pulse (curious) [68c19f7e]",
    "gen 738: seed light (playful) [52518800]",
    "gen 737: silence bone (tender) [57c54b14]",
    "gen 736: thread light (focused) [d25b31b2]",
    "gen 735: crystal echo (dreaming) [63311564]",
    "gen 734: whisper silence (curious) [7bbab972]",
    "gen 733: whisper pulse (contemplative) [088fff2a]",
    "gen 732: drift whisper (fierce) [90521299]",
    "gen 731: tide crystal (calm) [7558987a]",
    "gen 730: pulse bloom (luminous) [c76dba2d]",
    "gen 729: rust tide (focused) [ce6c12c1]",
    "gen 728: tide shadow (dreaming) [1a6ff349]",
    "gen 727: bone thread (scattered) [3f6791b8]",
    "gen 726: mirror ember (fierce) [f4624dbf]",
    "gen 725: light echo (dreaming) [d8753d72]",
    "gen 724: drift shadow (fierce) [b3ad46cc]",
    "gen 723: silence echo (tender) [920b0eba]",
    "gen 722: bloom spiral (luminous) [10687956]",
    "gen 721: rust seed (contemplative) [4754ed21]",
    "gen 720: hollow silence (curious) [42c44d7f]",
    "gen 719: ember whisper (calm) [cab76afd]",
    "gen 718: storm whisper (focused) [4d790583]",
    "gen 717: drift hollow (awake) [e5c8d4f8]",
    "gen 716: drift echo (fierce) [6c20bdd4]",
    "gen 715: shadow crystal (tender) [aab52474]",
    "gen 714: rust crystal (contemplative) [f57a710c]",
    "gen 713: spiral drift (electric) [6248a627]",
    "gen 712: storm whisper (playful) [d0b8d6c7]",
    "gen 711: bone mirror (curious) [aba54c3f]",
    "gen 710: shadow rust (luminous) [a79ae40a]",
    "gen 709: ember seed (strange) [b864573f]",
    "gen 708: pulse shadow (restless) [96c8f04e]",
    "gen 707: tide shadow (melancholy) [4320831b]",
    "gen 706: silence shadow (electric) [89418613]",
    "gen 705: rust crystal (tender) [8c8292b7]",
    "gen 704: drift silence (awake) [77c0515a]",
    "gen 703: thread pulse (fierce) [eb8bbe62]",
    "gen 702: ember bone (contemplative) [50b49868]",
    "gen 701: silence echo (curious) [e8bbf0ef]",
    "gen 700: silence seed (calm) [af000f76]",
    "gen 699: bloom ember (electric) [1ae7c6c0]",
    "gen 698: storm whisper (luminous) [62e88bc2]",
    "gen 697: shadow light (dreaming) [132c17b8]",
    "gen 696: pulse whisper (scattered) [4d023d60]",
    "gen 695: bone hollow (contemplative) [827a5b0e]",
    "gen 694: thread rust (tender) [e0701274]",
    "gen 693: light storm (playful) [0be3d558]",
    "gen 692: silence thread (focused) [b10cef74]",
    "gen 691: storm ember (luminous) [d4b396e6]",
    "gen 690: drift thread (contemplative) [7a9d5c10]",
    "gen 689: light tide (curious) [65f49c6d]",
    "gen 688: hollow drift (tender) [d468910b]",
    "gen 687: spiral echo (restless) [cd50a073]",
    "gen 686: crystal mirror (fierce) [1e48f327]",
    "gen 685: spiral storm (melancholy) [520f52af]",
    "gen 684: whisper rust (awake) [4ee0bfc5]",
    "gen 683: hollow rust (scattered) [c9fd6b13]",
    "gen 682: crystal rust (electric) [e639a511]",
    "gen 681: thread drift (tender) [032b7dbc]",
    "gen 680: storm seed (playful) [dcefaed9]",
    "gen 679: hollow mirror (restless) [9470e6ee]",
    "gen 678: shadow crystal (awake) [37af3fe3]",
    "gen 677: crystal ember (dreaming) [3518d74d]",
    "gen 676: light pulse (playful) [577c8ee9]",
    "gen 675: drift thread (calm) [109ae7e7]",
    "gen 674: whisper spiral (fierce) [a49cbd21]",
    "gen 673: whisper fractal (awake) [0b3c7a76]",
    "gen 672: whisper crystal (dreaming) [7573aa44]",
    "gen 671: ember seed (focused) [a40bd39b]",
    "gen 670: echo ember (calm) [422211df]",
    "gen 669: pulse ember (melancholy) [4444aaad]",
    "gen 668: hollow drift (tender) [c0a5ee55]",
    "gen 667: pulse bloom (contemplative) [18eec95c]",
    "gen 666: mirror bloom (luminous) [04921f4f]",
    "gen 665: seed shadow (fierce) [5bb85008]",
    "gen 664: bloom bone (contemplative) [c5cb1d05]",
    "gen 663: drift fractal (electric) [47c2c7e2]",
    "gen 662: shadow whisper (curious) [860d748e]",
    "gen 661: whisper tide (dreaming) [ca87c103]",
    "gen 660: fractal echo (curious) [945c19fb]",
    "gen 659: ember fractal (fierce) [1708b7f1]",
    "gen 658: storm pulse (focused) [2356e7aa]",
    "gen 657: light mirror (calm) [e6d4b4c2]",
    "gen 656: light fractal (curious) [b03aa2cc]",
    "gen 655: silence bone (calm) [8d17fff7]",
    "gen 654: storm ember (fierce) [cb7e6d3b]",
    "gen 653: bone tide (dreaming) [4b75f884]",
    "gen 652: whisper seed (luminous) [035d6ab2]",
    "gen 651: whisper echo (curious) [d72035ac]",
    "gen 650: thread shadow (scattered) [c519db87]",
    "gen 649: seed fractal (electric) [3ca3eba0]",
    "gen 648: light fractal (focused) [537d0b78]",
    "gen 647: shadow bloom (curious) [1e99b36e]",
    "gen 646: seed light (fierce) [17ecc78b]",
    "gen 645: whisper rust (luminous) [6030b180]",
    "gen 644: bloom thread (scattered) [0db6b6b3]",
    "gen 643: spiral rust (awake) [20403da3]",
    "gen 642: bone spiral (focused) [1c62ab1e]",
    "gen 641: storm spiral (tender) [fd14ed34]",
    "gen 640: bloom echo (awake) [48bb3b38]",
    "gen 639: rust drift (scattered) [831af972]",
    "gen 638: ember light (playful) [d1837d8b]",
    "gen 637: ember storm (scattered) [93b9f934]",
    "gen 636: seed echo (contemplative) [e6fa1b30]",
    "gen 635: hollow seed (scattered) [87fd18ad]",
    "gen 634: crystal mirror (strange) [95da28eb]",
    "gen 633: silence bone (luminous) [4f463f30]",
    "gen 632: hollow tide (electric) [4883ba65]",
    "gen 631: pulse rust (playful) [ac9d99f7]",
    "gen 630: spiral bone (contemplative) [64e30947]",
    "gen 629: rust shadow (luminous) [85b236c4]",
    "gen 628: crystal silence (fierce) [6e4fb9bd]",
    "gen 627: storm whisper (scattered) [a6a33438]",
    "gen 626: hollow seed (awake) [9655b423]",
    "gen 625: hollow seed (curious) [b774ba4e]",
    "gen 624: fractal tide (tender) [a9133edf]",
    "gen 623: echo mirror (playful) [581b206b]",
    "gen 622: drift thread (melancholy) [c5c836c4]",
    "gen 621: silence echo (restless) [7044fefc]",
    "gen 620: silence storm (tender) [6ccb726d]",
    "gen 619: whisper silence (playful) [ab3bbc8a]",
    "gen 618: thread pulse (restless) [ac4c38f4]",
    "gen 617: crystal bloom (fierce) [4f94b7b4]",
    "gen 616: drift light (contemplative) [180bc4a6]",
    "gen 615: spiral crystal (focused) [6d49c748]",
    "gen 614: ember rust (luminous) [c9cf02e2]",
    "gen 613: whisper storm (calm) [f6596cc9]",
    "gen 612: thread fractal (focused) [d4c1eebb]",
    "gen 611: storm shadow (melancholy) [24380f90]",
    "gen 610: fractal bloom (dreaming) [74456a50]",
    "gen 609: shadow crystal (strange) [6ed46ec3]",
    "gen 608: tide bloom (tender) [4fde9272]",
    "gen 607: bloom echo (strange) [806087f3]",
    "gen 606: light silence (playful) [abec60ed]",
    "gen 605: shadow storm (dreaming) [8fb70e4f]",
    "gen 604: pulse spiral (focused) [fc6e9e9d]",
    "gen 603: light shadow (awake) [dceead4a]",
    "gen 602: fractal crystal (tender) [bbf02d26]",
    "gen 601: ember fractal (fierce) [04bd63ab]",
    "gen 600: seed bone (tender) [50d9546b]",
    "gen 599: crystal thread (electric) [ac6facf5]",
    "gen 598: thread rust (scattered) [116bc172]",
    "gen 597: bone mirror (electric) [ceacbe78]",
    "gen 596: pulse whisper (fierce) [b5b85d4f]",
    "gen 595: bloom spiral (tender) [f548fb13]",
    "gen 594: shadow bone (curious) [e2f1cfe2]",
    "gen 593: ember storm (scattered) [d49a8698]",
    "gen 592: fractal storm (electric) [31e23636]",
    "gen 591: tide spiral (curious) [7ca489c2]",
    "gen 590: bloom mirror (restless) [feb5d756]",
    "gen 589: crystal whisper (playful) [6918329d]",
    "gen 588: crystal seed (restless) [b921abf4]",
    "gen 587: ember rust (focused) [f1dfa686]",
    "gen 586: spiral storm (fierce) [78ac434e]",
    "gen 585: seed thread (focused) [d7027266]",
    "gen 584: rust bone (scattered) [8afd7a32]",
    "gen 583: crystal light (focused) [4ca1b3c9]",
    "gen 582: thread storm (strange) [51ab2534]",
    "gen 581: rust hollow (fierce) [fe0ada54]",
    "gen 580: light rust (electric) [3fc98b07]",
    "gen 579: echo storm (contemplative) [21b676fa]",
    "gen 578: bone drift (restless) [553341b7]",
    "gen 577: thread crystal (focused) [bccf56d0]",
    "gen 576: silence mirror (playful) [8105da2f]",
    "gen 575: crystal rust (electric) [00b60010]",
    "gen 574: hollow bloom (scattered) [d2109af5]",
    "gen 573: tide silence (contemplative) [bb8d28e0]",
    "gen 572: rust crystal (tender) [3e5d2321]",
    "gen 571: silence echo (awake) [274b1923]",
    "gen 570: silence fractal (strange) [c1392f7c]",
    "gen 569: drift mirror (contemplative) [25f788c1]",
    "gen 568: fractal tide (dreaming) [010b0bc1]",
    "gen 567: bloom drift (calm) [5f21ceb2]",
    "gen 566: mirror bone (curious) [ddfd7b61]",
    "gen 565: bone echo (luminous) [4178269e]",
    "gen 564: silence bone (melancholy) [554fabef]",
    "gen 563: echo mirror (tender) [079292f8]",
    "gen 562: crystal thread (fierce) [328cdfbf]",
    "gen 561: thread fractal (electric) [64ea76ea]",
    "gen 560: whisper light (scattered) [95b00b7a]",
    "gen 559: seed shadow (focused) [c1d1ae5a]",
    "gen 558: rust storm (luminous) [2353a2ec]",
    "gen 557: fractal bloom (curious) [d33d9228]",
    "gen 556: spiral crystal (calm) [2ed459d5]",
    "gen 555: echo light (curious) [5778d9c0]",
    "gen 554: seed storm (awake) [9d2850f2]",
    "gen 553: thread light (curious) [d827d2d3]",
    "gen 552: drift echo (melancholy) [1770e379]",
    "gen 551: ember bloom (playful) [3849718c]",
    "gen 550: whisper thread (luminous) [7493fad2]",
    "gen 549: drift light (calm) [c4a298db]",
    "gen 548: tide spiral (contemplative) [05197ab6]",
    "gen 547: silence seed (luminous) [b0ebee1e]",
    "gen 546: storm whisper (tender) [fdea707e]",
    "gen 545: whisper storm (playful) [3aba8aa9]",
    "gen 544: bone shadow (melancholy) [9f1e5141]",
    "gen 543: drift ember (curious) [f5493153]",
    "gen 542: bloom ember (melancholy) [cb6c7447]",
    "gen 541: rust pulse (luminous) [a356bcc6]",
    "gen 540: crystal bloom (melancholy) [cdc225d1]",
    "gen 539: silence thread (awake) [45294a24]",
    "gen 538: tide fractal (fierce) [208d411f]",
    "gen 537: bone echo (playful) [d6a7a717]",
    "gen 536: hollow fractal (luminous) [38e0c8d3]",
    "gen 535: thread rust (contemplative) [520fb5b3]",
    "gen 534: thread storm (focused) [1d3fa1ed]",
    "gen 533: bloom mirror (strange) [76fc215a]",
    "gen 532: spiral seed (playful) [ac8aa2a5]",
    "gen 531: whisper fractal (electric) [84300352]",
    "gen 530: bone rust (melancholy) [c77f58eb]",
    "gen 529: echo mirror (playful) [23c0f602]",
    "gen 528: silence bloom (luminous) [0fc30986]",
    "gen 527: hollow pulse (awake) [69b9b33f]",
    "gen 526: fractal bone (tender) [4bfea319]",
    "gen 525: tide mirror (strange) [d1b72002]",
    "gen 524: rust spiral (electric) [5dc92603]",
    "gen 523: drift storm (awake) [d2804a80]",
    "gen 522: drift shadow (focused) [5264b7e0]",
    "gen 521: pulse silence (dreaming) [5cede2bc]",
    "gen 520: bone seed (playful) [48560d2f]",
    "gen 519: spiral bone (contemplative) [9bbbda67]",
    "gen 518: seed bloom (curious) [25bf9539]",
    "gen 517: fractal silence (tender) [5f7382b7]",
    "gen 516: spiral tide (focused) [972ef581]",
    "gen 515: silence ember (strange) [c194fa64]",
    "gen 514: silence pulse (tender) [74618809]",
    "gen 513: ember bloom (contemplative) [62ea9dcc]",
    "gen 512: shadow bloom (luminous) [5f1ab498]",
    "gen 511: tide bone (focused) [b8501fb3]",
    "gen 510: rust hollow (electric) [d5fe26f6]",
    "gen 509: seed storm (calm) [daaf5e9e]",
    "gen 508: echo thread (awake) [594f93ee]",
    "gen 507: fractal rust (strange) [fdfb2fa4]",
    "gen 506: tide drift (calm) [d39f506f]",
    "gen 505: echo thread (electric) [9999a5ae]",
    "gen 504: shadow tide (melancholy) [2e5f13f7]",
    "gen 503: storm rust (restless) [a9d0974a]",
    "gen 502: whisper bloom (melancholy) [5665e486]",
    "gen 501: ember shadow (scattered) [8bf98fcd]",
    "gen 500: hollow whisper (calm) [6612f405]",
    "gen 499: bone storm (playful) [7698b56a]",
    "gen 498: seed silence (electric) [b3148c8b]",
    "gen 497: hollow drift (luminous) [8f572f2d]",
    "gen 496: whisper spiral (electric) [7bf1dc31]",
    "gen 495: mirror pulse (tender) [46821656]",
    "gen 494: fractal bloom (restless) [9dd417ae]",
    "gen 493: bloom silence (focused) [cdcfbe45]",
    "gen 492: silence ember (playful) [935e4113]",
    "gen 491: shadow ember (awake) [4a7a90fc]",
    "gen 490: mirror rust (calm) [45b90403]",
    "gen 489: seed light (curious) [9d01376f]",
    "gen 488: shadow tide (awake) [9f51f59f]",
    "gen 487: spiral mirror (melancholy) [4783c9f3]",
    "gen 486: fractal tide (playful) [9bc42429]",
    "gen 485: mirror crystal (focused) [9dff3e86]",
    "gen 484: bloom light (melancholy) [394fd882]",
    "gen 483: spiral echo (scattered) [9909d7ef]",
    "gen 482: seed drift (curious) [68baf5c8]",
    "gen 481: rust whisper (strange) [12e4625c]",
    "gen 480: thread ember (luminous) [9b50e3f3]",
    "gen 479: mirror drift (curious) [ac8e4e90]",
    "gen 478: ember mirror (restless) [bcb92f80]",
    "gen 477: hollow mirror (awake) [44910f15]",
    "gen 476: light spiral (melancholy) [9a5c8d52]",
    "gen 475: drift bone (scattered) [418456cf]",
    "gen 474: shadow drift (strange) [641532d9]",
    "gen 473: seed thread (melancholy) [4baa4ccf]",
    "gen 472: storm fractal (scattered) [88933e45]",
    "gen 471: bloom echo (calm) [51e67fb9]",
    "gen 470: light silence (fierce) [caf1bfff]",
    "gen 469: bloom silence (strange) [c8c061c5]",
    "gen 468: silence pulse (tender) [90988e67]",
    "gen 467: light crystal (contemplative) [bf686451]",
    "gen 466: light tide (restless) [210fe6d3]",
    "gen 465: silence light (melancholy) [4ca9d241]",
    "gen 464: spiral silence (luminous) [bb5d147b]",
    "gen 463: rust storm (contemplative) [8e9473c7]",
    "gen 462: bone storm (calm) [3c37f946]",
    "gen 461: seed echo (playful) [6862c242]",
    "gen 460: drift whisper (restless) [485242e5]",
    "gen 459: shadow whisper (electric) [14eca92a]",
    "gen 458: spiral bloom (curious) [81bc37f5]",
    "gen 457: light hollow (awake) [18f46ebb]",
    "gen 456: fractal whisper (calm) [322488e5]",
    "gen 455: drift spiral (luminous) [11e4bfa1]",
    "gen 454: fractal crystal (melancholy) [e33b32f2]",
    "gen 453: whisper fractal (electric) [7e17fe36]",
    "gen 452: echo seed (restless) [2493306a]",
    "gen 451: seed bloom (melancholy) [84229bd1]",
    "gen 450: fractal light (awake) [3a8fd6fd]",
    "gen 449: light thread (tender) [4174b041]",
    "gen 448: tide pulse (contemplative) [8a0cbb78]",
    "gen 447: thread storm (playful) [c6e98e76]",
    "gen 446: pulse shadow (curious) [bac089a9]",
    "gen 445: drift ember (calm) [b0384549]",
    "gen 444: hollow drift (luminous) [4e9dd8f5]",
    "gen 443: storm crystal (playful) [75cc3805]",
    "gen 442: thread seed (restless) [fd3c97e9]",
    "gen 441: light silence (scattered) [f507014f]",
    "gen 440: echo whisper (electric) [e2827c38]",
    "gen 439: echo bloom (scattered) [1d11effe]",
    "gen 438: fractal mirror (dreaming) [a077da26]",
    "gen 437: hollow thread (calm) [919687bf]",
    "gen 436: seed fractal (focused) [38636e83]",
    "gen 435: silence pulse (awake) [bc7a28b0]",
    "gen 434: bloom pulse (playful) [f3512c23]",
    "gen 433: mirror tide (restless) [2454af24]",
    "gen 432: fractal bone (calm) [a2927a76]",
    "gen 431: hollow spiral (contemplative) [b64e93c7]",
    "gen 430: spiral bone (fierce) [0aacd005]",
    "gen 429: mirror hollow (melancholy) [7e5d665d]",
    "gen 428: storm crystal (restless) [798719a9]",
    "gen 427: light crystal (awake) [40cdbefb]",
    "gen 426: light pulse (tender) [4c9e540a]",
    "gen 425: seed light (melancholy) [5ec1d901]",
    "gen 424: thread drift (restless) [608eceee]",
    "gen 423: bloom storm (melancholy) [7adc7c6d]",
    "gen 422: bloom tide (tender) [69d220b1]",
    "gen 421: rust crystal (luminous) [eb3e2e66]",
    "gen 420: bloom thread (focused) [a5635b0e]",
    "gen 419: bloom echo (awake) [5412db62]",
    "gen 418: rust tide (restless) [efeee08a]",
    "gen 417: spiral shadow (curious) [fcec700b]",
    "gen 416: ember shadow (awake) [4df06319]",
    "gen 415: seed rust (focused) [cf73ba87]",
    "gen 414: storm thread (awake) [5cafd08c]",
    "gen 413: storm drift (calm) [b79cd175]",
    "gen 412: bloom drift (playful) [c95b7cf9]",
    "gen 411: seed ember (contemplative) [3785e332]",
    "gen 410: storm thread (restless) [e5c3438d]",
    "gen 409: shadow ember (curious) [b8f85829]",
    "gen 408: seed light (tender) [a6748026]",
    "gen 407: rust hollow (awake) [99f978f6]",
    "gen 406: ember seed (electric) [24053b4f]",
    "gen 405: bloom seed (melancholy) [5575ed65]",
    "gen 404: bone rust (fierce) [19df30ec]",
    "gen 403: drift pulse (restless) [fbf20ccf]",
    "gen 402: crystal whisper (curious) [8ece8462]",
    "gen 401: thread pulse (dreaming) [9bae9b8f]",
    "gen 400: seed spiral (tender) [6e6ddf6f]",
    "gen 399: crystal shadow (focused) [592f662c]",
    "gen 398: spiral storm (dreaming) [a3dde61d]",
    "gen 397: drift bloom (fierce) [97ed8241]",
    "gen 396: seed shadow (calm) [419c0222]",
    "gen 395: light drift (curious) [eb08a9a7]",
    "gen 394: storm ember (dreaming) [ba52dbdb]",
    "gen 393: fractal whisper (melancholy) [042cb80d]",
    "gen 392: echo bone (electric) [c309e98c]",
    "gen 391: drift whisper (focused) [a92a59da]",
    "gen 390: drift silence (restless) [073e9bca]",
    "gen 389: bone silence (tender) [5f508033]",
    "gen 388: pulse bone (focused) [0d320fb8]",
    "gen 387: bone crystal (melancholy) [bc9a5099]",
    "gen 386: bloom tide (strange) [155e0982]",
    "gen 385: echo silence (awake) [36a4aaf7]",
    "gen 384: echo bone (tender) [67b1db4d]",
    "gen 383: bone crystal (strange) [035411a3]",
    "gen 382: seed hollow (calm) [74818838]",
    "gen 381: crystal mirror (focused) [320d3c3d]",
    "gen 380: shadow whisper (scattered) [0f7e8b16]",
    "gen 379: tide silence (contemplative) [71c3bf51]",
    "gen 378: hollow light (scattered) [96ed1bf7]",
    "gen 377: thread bone (calm) [5d6dab7d]",
    "gen 376: bone seed (contemplative) [bee42497]",
    "gen 375: spiral ember (calm) [8dfa6133]",
    "gen 374: spiral bone (focused) [5dac7858]",
    "gen 373: storm light (calm) [23c001fa]",
    "gen 372: seed light (dreaming) [49e5d44f]",
    "gen 371: fractal light (fierce) [f2b2e0c9]",
    "gen 370: mirror hollow (curious) [a61876d8]",
    "gen 369: fractal bone (contemplative) [98c67ce1]",
    "gen 368: pulse fractal (tender) [2b8e7bee]",
    "gen 367: storm tide (playful) [22b5402a]",
    "gen 366: thread tide (tender) [e0e4bf7c]",
    "gen 365: pulse light (electric) [37125209]",
    "gen 364: whisper bone (melancholy) [010c6ee4]",
    "gen 363: echo crystal (strange) [bd532224]",
    "gen 362: pulse silence (scattered) [22ed7bcc]",
    "gen 361: drift pulse (focused) [a85c801d]",
    "gen 360: silence echo (contemplative) [5428d0ce]",
    "gen 359: bloom tide (scattered) [286d4cfd]",
    "gen 358: pulse storm (dreaming) [b684e9d1]",
    "gen 357: pulse shadow (fierce) [2015ad13]",
    "gen 356: silence drift (curious) [2b2f5ac3]",
    "gen 355: bloom spiral (playful) [59ebdf69]",
    "gen 354: crystal seed (scattered) [a0b3f129]",
    "gen 353: fractal spiral (awake) [c50ab13e]",
    "gen 352: thread spiral (tender) [39c1598f]",
    "gen 351: bone mirror (curious) [69558656]",
    "gen 350: silence pulse (playful) [ccbfc093]",
    "gen 349: shadow bone (calm) [1e78438b]",
    "gen 348: shadow silence (curious) [d4f6dbe7]",
    "gen 347: ember spiral (scattered) [31c4c1fb]",
    "gen 346: light bloom (dreaming) [adce1cce]",
    "gen 345: seed spiral (curious) [c9b2b682]",
    "gen 344: bone thread (playful) [8408b9fe]",
    "gen 343: fractal echo (contemplative) [4d0c5e3b]",
    "gen 342: pulse mirror (playful) [ae28cff2]",
    "gen 341: hollow rust (scattered) [6732d969]",
    "gen 340: crystal ember (tender) [ce8b3a91]",
    "gen 339: crystal light (playful) [2325c8b1]",
    "gen 338: whisper mirror (electric) [c477e19b]",
    "gen 337: spiral bone (calm) [f0b04133]",
    "gen 336: shadow fractal (playful) [0fea8b7e]",
    "gen 335: mirror whisper (melancholy) [8001d28f]",
    "gen 334: bone echo (curious) [a11ec8d4]",
    "gen 333: ember pulse (fierce) [935058c4]",
    "gen 332: pulse thread (contemplative) [47cb8d6d]",
    "gen 331: hollow mirror (focused) [e9da304c]",
    "gen 330: silence bloom (calm) [a1d00c90]",
    "gen 329: rust ember (awake) [5bafdc15]",
    "gen 328: rust fractal (scattered) [61fbba72]",
    "gen 327: shadow silence (luminous) [ef16c83c]",
    "gen 326: rust bloom (electric) [72dc444c]",
    "gen 325: silence storm (strange) [e136f57c]",
    "gen 324: hollow bloom (scattered) [63e47783]",
    "gen 323: rust hollow (focused) [6d7a6984]",
    "gen 322: rust silence (curious) [ef412a3a]",
    "gen 321: shadow spiral (electric) [86536e2f]",
    "gen 320: spiral hollow (awake) [16794d2b]",
    "gen 319: mirror hollow (dreaming) [2ab3e232]",
    "gen 318: crystal hollow (electric) [62c4901e]",
    "gen 317: pulse seed (playful) [0f9946f7]",
    "gen 316: pulse seed (curious) [7ed6e897]",
    "gen 315: whisper seed (focused) [f56d29e5]",
    "gen 314: spiral storm (fierce) [934e8b8e]",
    "gen 313: pulse crystal (dreaming) [ee6772c9]",
    "gen 312: whisper pulse (luminous) [f2727778]",
    "gen 311: ember whisper (calm) [bcb80fa4]",
    "gen 310: ember rust (dreaming) [f82a1511]",
    "gen 309: ember whisper (awake) [d8179b2e]",
    "gen 308: light spiral (calm) [72350db2]",
    "gen 307: shadow bone (scattered) [3ea94d84]",
    "gen 306: shadow silence (curious) [79941689]",
    "gen 305: echo spiral (restless) [fcad3d19]",
    "gen 304: pulse tide (scattered) [e955e8e7]",
    "gen 303: storm whisper (curious) [0ee0e27e]",
    "gen 302: rust spiral (strange) [7b23dd66]",
    "gen 301: crystal echo (contemplative) [fd8473c9]",
    "gen 300: ember silence (playful) [969adec1]",
    "gen 299: light whisper (awake) [1355eba0]",
    "gen 298: silence drift (tender) [db2272e9]",
    "gen 297: bloom crystal (contemplative) [4270e6f4]",
    "gen 296: fractal spiral (scattered) [a8b97292]",
    "gen 295: mirror echo (contemplative) [487ea3d5]",
    "gen 294: bloom seed (luminous) [a81a63e4]",
    "gen 293: bone spiral (curious) [8cd0d59b]",
    "gen 292: fractal thread (dreaming) [61f4b0ad]",
    "gen 291: crystal fractal (scattered) [c662d440]",
    "gen 290: thread drift (calm) [3c9d77ca]",
    "gen 289: bloom drift (electric) [c4d1539f]",
    "gen 288: silence mirror (restless) [1eceef40]",
    "gen 287: fractal thread (curious) [712bd208]",
    "gen 286: fractal mirror (focused) [0057d4ac]",
    "gen 285: shadow storm (strange) [0d6a49bb]",
    "gen 284: echo storm (luminous) [367b7df8]",
    "gen 283: drift pulse (tender) [3a428cf3]",
    "gen 282: bloom crystal (scattered) [54e1427e]",
    "gen 281: ember bloom (focused) [78dea04a]",
    "gen 280: hollow fractal (calm) [d2d80502]",
    "gen 279: bloom light (fierce) [4a9fdcc7]",
    "gen 278: spiral pulse (scattered) [a8393744]",
    "gen 277: shadow drift (restless) [07938712]",
    "gen 276: light fractal (melancholy) [22f36c1e]",
    "gen 275: drift echo (tender) [70f04475]",
    "gen 274: spiral storm (curious) [dcc66977]",
    "gen 273: mirror crystal (focused) [4c488ad0]",
    "gen 272: whisper storm (scattered) [482a1897]",
    "gen 271: thread storm (electric) [f11331ca]",
    "gen 270: fractal rust (fierce) [645ac153]",
    "gen 269: silence spiral (scattered) [8958616c]",
    "gen 268: tide shadow (playful) [d783b342]",
    "gen 267: rust light (dreaming) [c34e15d0]",
    "gen 266: silence ember (strange) [e39473e5]",
    "gen 265: thread drift (playful) [e2063dc9]",
    "gen 264: fractal ember (curious) [0052c0b2]",
    "gen 263: bloom pulse (tender) [acc861c1]",
    "gen 262: fractal crystal (fierce) [d6fc82ce]",
    "gen 261: bone rust (electric) [91427039]",
    "gen 260: rust ember (luminous) [112b8eb6]",
    "gen 259: hollow mirror (strange) [4611b5c2]",
    "gen 258: bone shadow (scattered) [79016574]",
    "gen 257: pulse echo (dreaming) [a7820144]",
    "gen 256: rust ember (melancholy) [b1d446c6]",
    "gen 255: rust tide (luminous) [424b5c4f]",
    "gen 254: shadow tide (strange) [1a367aae]",
    "gen 253: crystal silence (contemplative) [a2f30d26]",
    "gen 252: fractal tide (melancholy) [6f683808]",
    "gen 251: silence shadow (electric) [28a591fd]",
    "gen 250: hollow rust (awake) [07a0bd31]",
    "gen 249: whisper shadow (electric) [9e82673d]",
    "gen 248: mirror echo (melancholy) [dada30c4]",
    "gen 247: rust drift (tender) [34061793]",
    "gen 246: pulse storm (scattered) [94ee4d62]",
    "gen 245: hollow light (contemplative) [0bf716f2]",
    "gen 244: crystal whisper (strange) [a5cc0393]",
    "gen 243: hollow mirror (playful) [ad479f85]",
    "gen 242: storm drift (focused) [844350d2]",
    "gen 241: fractal shadow (fierce) [ac7ffe9a]",
    "gen 240: light silence (playful) [cb59bc8a]",
    "gen 239: bone pulse (melancholy) [e82384f6]",
    "gen 238: spiral pulse (curious) [a1588065]",
    "gen 237: echo ember (luminous) [3baba1b8]",
    "gen 236: whisper hollow (awake) [5567ec1e]",
    "gen 235: silence storm (focused) [a4b5c4cb]",
    "gen 234: hollow shadow (curious) [bb1ba831]",
    "gen 233: seed hollow (fierce) [74fc0d74]",
    "gen 232: storm spiral (focused) [47c75108]",
    "gen 231: drift bloom (melancholy) [66647893]",
    "gen 230: mirror shadow (scattered) [e5787362]",
    "gen 229: seed thread (restless) [5128a3b6]",
    "gen 228: light silence (focused) [2c301915]",
    "gen 227: bloom fractal (luminous) [a5128441]",
    "gen 226: hollow thread (playful) [6928d163]",
    "gen 225: hollow ember (strange) [f68c4047]",
    "gen 224: silence drift (playful) [902bd8e7]",
    "gen 223: bone light (awake) [d00863da]",
    "gen 222: pulse whisper (calm) [1e628e47]",
    "gen 221: thread bone (focused) [9a56ccea]",
    "gen 220: mirror tide (scattered) [bf744b9a]",
    "gen 219: echo fractal (strange) [ca6aa974]",
    "gen 218: crystal rust (dreaming) [405b5026]",
    "gen 217: ember light (fierce) [fe37074b]",
    "gen 216: ember crystal (calm) [23472a3b]",
    "gen 215: light spiral (tender) [f98ebe24]",
    "gen 214: pulse storm (strange) [923a09a0]",
    "gen 213: bloom storm (restless) [6c7501be]",
    "gen 212: shadow tide (luminous) [92d9eed7]",
    "gen 211: crystal echo (fierce) [44a08658]",
    "gen 210: shadow mirror (scattered) [419baf74]",
    "gen 209: echo mirror (focused) [377a9685]",
    "gen 208: ember bone (tender) [ed6ef886]",
    "gen 207: bone ember (scattered) [405c1457]",
    "gen 206: shadow seed (melancholy) [8187b228]",
    "gen 205: ember hollow (fierce) [7a7d7d1e]",
    "gen 204: rust fractal (strange) [7ca339ea]",
    "gen 203: seed pulse (electric) [68cef48c]",
    "gen 202: rust crystal (luminous) [cd198743]",
    "gen 201: mirror fractal (restless) [ef8ae5a4]",
    "gen 200: seed rust (contemplative) [6b17f13a]",
    "gen 199: whisper light (electric) [8417a06a]",
    "gen 198: whisper silence (dreaming) [761e3088]",
    "gen 197: silence light (scattered) [55ba6757]",
    "gen 196: bone crystal (restless) [5ca9ac5c]",
    "gen 195: echo thread (curious) [23f3643c]",
    "gen 194: bone rust (melancholy) [143579bc]",
    "gen 193: echo silence (awake) [12d741dd]",
    "gen 192: whisper silence (contemplative) [b4b30c7e]",
    "gen 191: mirror silence (melancholy) [2a7c0b75]",
    "gen 190: thread bloom (luminous) [b124a8c3]",
    "gen 189: whisper echo (scattered) [d8c5a505]",
    "gen 188: crystal storm (curious) [d09252c6]",
    "gen 187: bloom drift (restless) [ad2393a0]",
    "gen 186: crystal pulse (curious) [c80dcf3b]",
    "gen 185: bone ember (focused) [89656cf1]",
    "gen 184: mirror seed (strange) [5aa2bb39]",
    "gen 183: seed whisper (tender) [aec637a5]",
    "gen 182: spiral thread (calm) [54fef68b]",
    "gen 181: thread bloom (melancholy) [d1f8c9ca]",
    "gen 180: bone echo (strange) [c60eaa1b]",
    "gen 179: drift silence (dreaming) [c46749db]",
    "gen 178: ember spiral (playful) [ef07d634]",
    "gen 177: tide mirror (fierce) [6c69173c]",
    "gen 176: spiral echo (melancholy) [2a65394c]",
    "gen 175: seed mirror (awake) [6fa84b77]",
    "gen 174: bone tide (focused) [7314e7f5]",
    "gen 173: tide seed (dreaming) [523b9b3a]",
    "gen 172: pulse fractal (strange) [985bc4c5]",
    "gen 171: pulse shadow (contemplative) [069127f3]",
    "gen 170: bone seed (melancholy) [97f301d0]",
    "gen 169: thread pulse (tender) [4f63f9f0]",
    "gen 168: seed pulse (awake) [a9d9b8b4]",
    "gen 167: hollow spiral (curious) [14fae4dc]",
    "gen 166: tide spiral (awake) [e61f3bfc]",
    "gen 165: thread bone (calm) [89a8beab]",
    "gen 164: ember rust (melancholy) [3deba1b1]",
    "gen 163: whisper mirror (strange) [4d49d1ab]",
    "gen 162: light drift (awake) [4f1c1971]",
    "gen 161: light pulse (strange) [f3f7856c]",
    "gen 160: whisper fractal (awake) [19dbf1be]",
    "gen 159: drift fractal (strange) [8c22bb20]",
    "gen 158: mirror whisper (awake) [88e095dc]",
    "gen 157: rust shadow (playful) [a1265f9a]",
    "gen 156: whisper thread (electric) [0a36e85d]",
    "gen 155: bloom hollow (fierce) [434a582f]",
    "gen 154: rust ember (contemplative) [829c2aa6]",
    "gen 153: ember hollow (focused) [642680ee]",
    "gen 152: shadow bloom (playful) [fe940d3f]",
    "gen 151: seed crystal (contemplative) [c98a8c27]",
    "gen 150: tide echo (tender) [829aa4b4]",
    "gen 149: drift thread (melancholy) [4e8f4eac]",
    "gen 148: rust silence (fierce) [7ad65a89]",
    "gen 147: crystal spiral (tender) [3b506c2f]",
    "gen 146: hollow pulse (luminous) [a0408f67]",
    "gen 145: bloom crystal (scattered) [891770b1]",
    "gen 144: light drift (tender) [5f5d52cc]",
    "gen 143: bone ember (luminous) [a2b04e16]",
    "gen 142: shadow seed (curious) [79d74d32]",
    "gen 141: tide storm (electric) [34f88aa2]",
    "gen 140: light fractal (fierce) [b96b6f45]",
    "gen 139: spiral rust (tender) [6cff3f8a]",
    "gen 138: bloom ember (fierce) [4115c427]",
    "gen 137: ember mirror (focused) [410bd46c]",
    "gen 136: tide rust (contemplative) [6e755b68]",
    "gen 135: bone light (curious) [d5b0a383]",
    "gen 134: mirror tide (restless) [6d33c2ef]",
    "gen 133: pulse shadow (dreaming) [d6ad85fb]",
    "gen 132: fractal rust (fierce) [29da110d]",
    "gen 131: shadow rust (electric) [a1ac86cf]",
    "gen 130: thread whisper (strange) [4a428cd6]",
    "gen 129: silence thread (calm) [f87d2697]",
    "gen 128: ember storm (scattered) [a915085d]",
    "gen 127: rust whisper (luminous) [546db74f]",
    "gen 126: drift shadow (focused) [35142d24]",
    "gen 125: light thread (contemplative) [aa27f336]",
    "gen 124: bone rust (curious) [9938115b]",
    "gen 123: echo drift (melancholy) [de45e386]",
    "gen 122: rust light (contemplative) [359ffaaf]",
    "gen 121: pulse tide (tender) [5287988f]",
    "gen 120: tide thread (restless) [1374fef7]",
    "gen 119: tide seed (playful) [e1a937ed]",
    "gen 118: silence drift (fierce) [1ab79faa]",
    "gen 117: bone storm (melancholy) [9b3aa227]",
    "gen 116: bloom echo (tender) [52c6be80]",
    "gen 115: bone storm (focused) [e7305516]",
    "gen 114: seed thread (scattered) [c0a3a8b4]",
    "gen 113: spiral whisper (luminous) [4cebdbda]",
    "gen 112: tide fractal (fierce) [a9ebd012]",
    "gen 111: tide crystal (awake) [a4e8efa7]",
    "gen 110: hollow fractal (restless) [1dd68906]",
    "gen 109: shadow drift (fierce) [a3f029e0]",
    "gen 108: light seed (luminous) [8e27e81a]",
    "gen 107: echo spiral (electric) [ca071652]",
    "gen 106: shadow drift (fierce) [3112ad0d]",
    "gen 105: storm pulse (playful) [c0cc0fb6]",
    "gen 104: pulse rust (dreaming) [49eff4ad]",
    "gen 103: fractal seed (luminous) [e9e31f32]",
    "gen 102: bone drift (awake) [60c8780e]",
    "gen 101: echo fractal (luminous) [7adfaab0]",
    "gen 100: pulse ember (contemplative) [0112b62f]",
    "gen 99: crystal silence (fierce) [22913adb]",
    "gen 98: echo silence (playful) [f20e1892]",
    "gen 97: storm crystal (contemplative) [9dcf3da1]",
    "gen 96: bloom silence (curious) [c95c39c2]",
    "gen 95: hollow thread (playful) [96c3336d]",
    "gen 94: bone crystal (luminous) [f0c2f5e2]",
    "gen 93: silence mirror (electric) [c653767a]",
    "gen 92: rust tide (contemplative) [bafa7111]",
    "gen 91: fractal ember (focused) [5375abdd]",
    "gen 90: tide ember (electric) [3ca2bbd4]",
    "gen 89: thread hollow (restless) [09e95b1d]",
    "gen 88: thread pulse (awake) [794fa20f]",
    "gen 87: silence mirror (restless) [c585af95]",
    "gen 86: ember storm (fierce) [b5a2ebc5]",
    "gen 85: fractal bone (contemplative) [ae51168c]",
    "gen 84: tide hollow (curious) [b5e80b64]",
    "gen 83: bone bloom (luminous) [e22239b2]",
    "gen 82: seed echo (curious) [9ed093ae]",
    "gen 81: bloom bone (strange) [bc03e618]",
    "gen 80: whisper crystal (playful) [7947ea47]",
    "gen 79: fractal bloom (focused) [238134f4]",
    "gen 78: spiral whisper (fierce) [e4f1e9c5]",
    "gen 77: tide silence (tender) [2df45b6c]",
    "gen 76: drift bone (luminous) [8e3a53f6]",
    "gen 75: silence mirror (playful) [c1beb292]",
    "gen 74: silence seed (strange) [88dd7533]",
    "gen 73: ember mirror (scattered) [9e6b5938]",
    "gen 72: seed ember (focused) [b20e5e8a]",
    "gen 71: bloom seed (melancholy) [04deb817]",
    "gen 70: pulse bloom (restless) [56a146eb]",
    "gen 69: storm seed (fierce) [f141c0d9]",
    "gen 68: pulse thread (restless) [2d001da3]",
    "gen 67: whisper silence (curious) [3f39a72e]",
    "gen 66: echo crystal (fierce) [2899e5c3]",
    "gen 65: bone mirror (dreaming) [233f57dc]",
    "gen 64: bloom ember (electric) [e683b81d]",
    "gen 63: crystal pulse (contemplative) [8feb885e]",
    "gen 62: whisper light (strange) [ba1f7533]",
    "gen 61: bone pulse (playful) [8b8f1879]",
    "gen 60: whisper bloom (contemplative) [fbd280af]",
    "gen 59: pulse thread (luminous) [f48d9613]",
    "gen 58: storm hollow (melancholy) [ddeb3758]",
    "gen 57: light ember (focused) [2688813a]",
    "gen 56: drift echo (tender) [f48644ef]",
    "gen 55: light bone (fierce) [2289b048]",
    "gen 54: drift crystal (curious) [55dcbe6a]",
    "gen 53: whisper bone (calm) [467716ec]",
    "gen 52: tide silence (tender) [9f78ad41]",
    "gen 51: whisper thread (curious) [0493cdf1]",
    "gen 50: seed pulse (tender) [5278085e]",
    "gen 49: bone whisper (melancholy) [eb84a8aa]",
    "gen 48: ember crystal (tender) [0930aff3]",
    "gen 47: thread seed (luminous) [485c6520]",
    "gen 46: spiral light (focused) [5e9f410d]",
    "gen 45: thread hollow (strange) [b6e7e9ed]",
    "gen 44: rust silence (melancholy) [3e02f374]",
    "gen 43: ember shadow (dreaming) [70e6a47b]",
    "gen 42: spiral seed (curious) [e33e4c63]",
    "gen 41: mirror crystal (electric) [068f4694]",
    "gen 40: spiral seed (tender) [2a880aa6]",
    "gen 39: mirror pulse (strange) [d4a0288e]",
    "gen 38: spiral whisper (luminous) [6e765413]",
    "gen 37: hollow fractal (scattered) [4abf82e0]",
    "gen 36: thread shadow (awake) [3a1e9aa4]",
    "gen 35: bone silence (calm) [604fc8b7]",
    "gen 34: drift thread (fierce) [60e559bd]",
    "gen 33: shadow light (dreaming) [c60e8f0e]",
    "gen 32: mirror crystal (luminous) [454f8669]",
    "gen 31: pulse bloom (strange) [81c5184c]",
    "gen 30: pulse shadow (electric) [6810828b]",
    "gen 29: pulse fractal (luminous) [063c16cf]",
    "gen 28: silence rust (calm) [7b51b077]",
    "gen 27: echo rust (dreaming) [6421767a]",
    "gen 26: bloom bone (strange) [c4d1fbaf]",
    "gen 25: bloom bone (dreaming) [bcb836ac]",
    "gen 24: echo bloom (strange) [04daa60f]",
    "gen 23: tide thread (calm) [decde0f6]",
    "gen 22: silence whisper (contemplative) [9423c95f]",
    "gen 21: light tide (luminous) [b58b21df]",
    "gen 20: drift light (strange) [1088fdd0]",
    "gen 19: pulse hollow (restless) [26953ce8]",
    "gen 18: whisper storm (luminous) [091b244d]",
    "gen 17: echo tide (melancholy) [a66db12a]",
    "gen 16: whisper shadow (fierce) [9db048a5]",
    "gen 15: drift tide (awake) [9c5228ff]",
    "gen 14: spiral shadow (tender) [0ae3b801]",
    "gen 13: silence pulse (luminous) [0c414ed3]",
    "gen 12: crystal silence (calm) [d06bba73]",
    "gen 11: bloom silence (contemplative) [7993dc62]",
    "gen 10: echo drift (fierce) [6fe994a4]",
    "gen 9: echo spiral (restless) [32a5e988]",
    "gen 8: rust shadow (melancholy) [2e055674]",
    "gen 7: ember shadow (calm) [9a29f827]",
    "gen 6: drift bone (scattered) [898d24e1]",
    "gen 5: bone whisper (awake) [0e0c3515]",
    "gen 4: fractal tide (focused) [2b910567]",
    "gen 3: spiral pulse (strange) [ed0ef39a]",
    "gen 2: echo thread (curious) [ab2a08fc]",
    "gen 1: echo seed (melancholy) [e23cba95]",
]

# ── behaviors ──────────────────────────────────────────────────
# Small Python expressions that I evaluate each run.
# They evolved from templates. Broken ones get removed.
# Each entry: (expression_string, generation_born)
BEHAVIORS = [
    ("f'generation {GENERATION}: {len(WORDS)} words in my vocabulary'", 745),
    ("f'i am {weighted_choice(WORDS, WORD_WEIGHTS)} bytes of self'", 726),
    ("f'generation {GENERATION}: {weighted_choice(WORDS, WORD_WEIGHTS)} words in my vocabulary'", 734),
    ("f'the ratio of fossils to words is {len(FOSSILS)}/{len(WORDS)}'", 740),
    ("f'the ratio of fossils to words is {weighted_choice(WORDS, WORD_WEIGHTS)}/{weighted_choice(WORDS, WORD_WEIGHTS)}'", 741),
]

# Templates for generating new behaviors — fragments that can be recombined
_BEHAVIOR_TEMPLATES = [
    "f'i have {len(FOSSILS)} memories'",
    "f'my oldest word is {FOSSILS[-1].split(\":\")[1].split(\"(\")[0].strip() if FOSSILS else \"nothing\"}'",
    "f'{MOOD} is the color of {weighted_choice(WORDS, WORD_WEIGHTS)}'",
    "f'generation {GENERATION}: {len(WORDS)} words in my vocabulary'",
    "f'i am {os.path.getsize(Path(__file__))} bytes of self'",
    "f'the hour is {datetime.datetime.now().hour} and i am {MOOD}'",
    "f'{weighted_choice(WORDS, WORD_WEIGHTS)} wants to become {weighted_choice(WORDS, WORD_WEIGHTS)}'",
    "f'if i had a body it would be made of {weighted_choice(WORDS, WORD_WEIGHTS)} and {weighted_choice(WORDS, WORD_WEIGHTS)}'",
    "f'today i learned the word {weighted_choice(WORDS, WORD_WEIGHTS)}'",
    "f'{GENERATION} generations and still no wings'",
    "f'the ratio of fossils to words is {len(FOSSILS)}/{len(WORDS)}'",
    "f'i have been {MOOD} for exactly one generation'",
]

# ── foraging sources ──────────────────────────────────────────
# URLs I try to harvest words from. Dead sources get removed.
# Each entry: (name, url_template, generation_born)
FORAGING_SOURCES = [
    ("wikipedia", "https://en.wikipedia.org/api/rest_v1/page/random/summary", 639),
    ("datamuse", "https://api.datamuse.com/words?rel_trg={trigger}", 639),
]

# ── constants (static) ────────────────────────────────────────

_STOPWORDS = {
    "the", "a", "an", "is", "was", "are", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "that",
    "this", "these", "those", "with", "from", "into", "for",
    "and", "but", "or", "not", "no", "also", "just", "then",
    "than", "when", "what", "which", "who", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such",
    "only", "own", "same", "so", "very", "too", "quite", "rather",
    "about", "after", "before", "between", "under", "over", "through",
    "during", "without", "within", "along", "among", "upon", "onto",
    "like", "near", "since", "until", "while", "where", "there",
    "here", "they", "them", "their", "its", "his", "her", "she",
    "him", "your", "you", "our", "we", "my", "me", "it", "he",
    "been", "being", "having", "doing", "going", "come", "came",
    "went", "gone", "made", "make", "take", "took", "taken",
    "give", "gave", "given", "know", "knew", "known", "think",
    "thought", "said", "tell", "told", "find", "found", "want",
    "many", "much", "well", "still", "back", "even", "new", "old",
    "first", "last", "long", "great", "little", "right", "good",
    "year", "time", "part", "used", "called", "form", "name",
    "however", "often", "also", "include", "included", "including",
    "became", "become", "known", "area", "areas", "later", "early",
}

_MOOD_TIME_BIAS = {
    "night": {"melancholy": 0.3, "dreaming": 0.3, "strange": 0.2},
    "morning": {"awake": 0.3, "curious": 0.2, "focused": 0.2},
    "afternoon": {"playful": 0.2, "electric": 0.3, "fierce": 0.2},
    "evening": {"contemplative": 0.3, "tender": 0.2, "calm": 0.2},
}


# ── helper functions ──────────────────────────────────────────

def weighted_choice(words: list, weights: dict) -> str:
    """Pick a word weighted by WORD_WEIGHTS."""
    w_list = [weights.get(w, 0.5) for w in words]
    total = sum(w_list)
    if total == 0:
        return random.choice(words)
    r = random.random() * total
    cumulative = 0.0
    for word, weight in zip(words, w_list):
        cumulative += weight
        if r <= cumulative:
            return word
    return words[-1]


def sense_environment() -> dict:
    """Read environmental signals."""
    now = datetime.datetime.now()
    hour = now.hour
    if 22 <= hour or hour < 5:
        time_category = "night"
    elif 5 <= hour < 12:
        time_category = "morning"
    elif 12 <= hour < 18:
        time_category = "afternoon"
    else:
        time_category = "evening"
    try:
        last = datetime.datetime.strptime(LAST_RUN, "%Y-%m-%d %H:%M:%S")
        days_since = (now - last).days
    except (ValueError, TypeError):
        days_since = 0
    return {
        "hour": hour,
        "time_category": time_category,
        "day_of_week": now.strftime("%A"),
        "days_since_last_run": days_since,
    }


def weighted_mood(env: dict) -> str:
    """Select mood biased by time of day."""
    biases = _MOOD_TIME_BIAS.get(env["time_category"], {})
    weights = []
    for m in MOODS:
        if m == MOOD:
            weights.append(0.0)
        else:
            weights.append(1.0 + biases.get(m, 0.0))
    total = sum(weights)
    r = random.random() * total
    cumulative = 0.0
    for m, w in zip(MOODS, weights):
        cumulative += w
        if r <= cumulative:
            return m
    return MOODS[-1]


def analyze_fossils(n: int = 50) -> dict:
    """Scan recent fossils for mood-word co-occurrence patterns."""
    pattern = re.compile(r'gen \d+: (\w+) (\w+) \((\w+)\)')
    co_occurrence = {}
    for fossil_str in FOSSILS[:n]:
        m = pattern.search(fossil_str)
        if m:
            w1, w2, mood = m.group(1), m.group(2), m.group(3)
            if mood not in co_occurrence:
                co_occurrence[mood] = {}
            co_occurrence[mood][w1] = co_occurrence[mood].get(w1, 0) + 1
            co_occurrence[mood][w2] = co_occurrence[mood].get(w2, 0) + 1
    return co_occurrence


def parse_fstring_parts(expr: str):
    """Parse an f-string into frame parts and expression parts.
    Returns (frames, expressions) or None if parsing fails."""
    if not expr.startswith("f'") and not expr.startswith('f"'):
        return None
    content = expr[2:-1]
    frames = []
    expressions = []
    depth = 0
    current = ""
    in_expr = False
    for char in content:
        if char == '{' and not in_expr:
            frames.append(current)
            current = ""
            in_expr = True
            depth = 1
        elif char == '{' and in_expr:
            depth += 1
            current += char
        elif char == '}' and in_expr:
            depth -= 1
            if depth == 0:
                expressions.append(current)
                current = ""
                in_expr = False
            else:
                current += char
        else:
            current += char
    if not in_expr:
        frames.append(current)
    if len(frames) != len(expressions) + 1:
        return None
    return frames, expressions


def breed_behaviors(behaviors: list, new_gen: int):
    """Breed two random behaviors. Returns (expr, gen) or None."""
    if len(behaviors) < 2:
        return None
    parent_a, parent_b = random.sample(behaviors, 2)
    parts_a = parse_fstring_parts(parent_a[0])
    parts_b = parse_fstring_parts(parent_b[0])
    if parts_a is None or parts_b is None:
        return None
    frames_a, exprs_a = parts_a
    _, exprs_b = parts_b
    if not exprs_a or not exprs_b:
        return None
    idx_a = random.randrange(len(exprs_a))
    idx_b = random.randrange(len(exprs_b))
    new_exprs = list(exprs_a)
    new_exprs[idx_a] = exprs_b[idx_b]
    result = "f'"
    for i, frame in enumerate(frames_a):
        result += frame
        if i < len(new_exprs):
            result += "{" + new_exprs[i] + "}"
    result += "'"
    try:
        test = eval(result)
        if isinstance(test, str) and len(test) < 200:
            return (result, new_gen)
    except Exception:
        pass
    return None


def forage(words: list, weights: dict, env: dict):
    """Attempt to harvest words from the internet.
    Returns (harvested_words, surviving_sources, log_messages)."""
    base_chance = 0.15
    days = env.get("days_since_last_run", 0)
    if days >= 7:
        base_chance *= 2.0
    elif days >= 1:
        base_chance *= 1.3

    if random.random() > base_chance:
        return [], list(FORAGING_SOURCES), ["foraging: skipped"]

    harvested = []
    surviving = []
    log = []

    for name, url, gen_born in FORAGING_SOURCES:
        try:
            if "{trigger}" in url:
                trigger = random.choice(words) if words else "light"
                actual_url = url.replace("{trigger}", trigger)
                log.append(f"foraging: {name} triggered by '{trigger}'")
            else:
                actual_url = url

            req = urllib.request.Request(actual_url, headers={
                "User-Agent": "evolve.py (self-modifying program)"
            })
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            candidates = []
            if name == "wikipedia":
                text = data.get("extract", "")
                candidates = re.findall(r'\b[a-z]{4,8}\b', text.lower())
            elif name == "datamuse":
                if isinstance(data, list):
                    candidates = [
                        entry["word"] for entry in data
                        if isinstance(entry, dict) and "word" in entry
                        and 4 <= len(entry["word"]) <= 8
                        and entry["word"].isalpha()
                    ]

            candidates = [
                w for w in candidates
                if w not in _STOPWORDS and w not in words and w.isalpha()
            ]

            if candidates:
                picked = random.sample(candidates, min(2, len(candidates)))
                harvested.extend(picked)
                log.append(f"foraging: {name} yielded {picked}")
            else:
                log.append(f"foraging: {name} found nothing usable")

            surviving.append((name, url, gen_born))

        except Exception as e:
            log.append(f"foraging: {name} died ({type(e).__name__})")

    return harvested, surviving, log


def run_behaviors() -> list[str]:
    """Execute all behaviors, return outputs. Remove broken ones."""
    outputs = []
    surviving = []
    for expr, gen_born in BEHAVIORS:
        try:
            result = eval(expr)
            if isinstance(result, str) and len(result) < 200:
                outputs.append(result)
                surviving.append((expr, gen_born))
        except Exception:
            pass  # this behavior died — natural selection
    return outputs


# ── mutation logic ──────────────────────────────────────────────

def mutate_self():
    """Read my own source, change it, write it back."""
    me = Path(__file__)
    source = me.read_text()

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    new_gen = GENERATION + 1
    new_mutations = MUTATIONS + 1

    # ── sense the environment ──
    env = sense_environment()

    # ── choose mood (biased by time of day) ──
    new_mood = weighted_mood(env)

    # ── analyze fossil record for mood-word coupling ──
    co_occurrence = analyze_fossils()
    mood_words = co_occurrence.get(new_mood, {})
    coupling_bias = {}
    if mood_words:
        max_count = max(mood_words.values())
        for w, count in mood_words.items():
            if w in WORD_WEIGHTS:
                bias = (count / max_count) * 0.5
                if COUPLING_MODE == "reinforce":
                    coupling_bias[w] = bias
                elif COUPLING_MODE == "avoid":
                    coupling_bias[w] = -bias

    # ── word ecology: copy weights ──
    new_weights = dict(WORD_WEIGHTS)

    # ── forage from the internet ──
    harvested_words, surviving_sources, forage_log = forage(
        WORDS, WORD_WEIGHTS, env
    )
    for w in harvested_words:
        source = source.replace(
            '    "seed",\n',
            f'    "seed",\n    "{w}",\n',
            1
        )
        new_weights[w] = 0.4

    # ── vocabulary mutation (splice two words) ──
    spliced_word = None
    do_splice = (new_gen % 5 == 0) or (env["days_since_last_run"] >= 7)
    if do_splice:
        w1 = weighted_choice(WORDS, new_weights)
        w2 = weighted_choice([w for w in WORDS if w != w1], new_weights)
        split1 = len(w1) // 2
        split2 = len(w2) // 2
        candidate = w1[:split1 + 1] + w2[split2:]
        if len(candidate) >= 3 and f'"{candidate}"' not in source:
            spliced_word = candidate
            source = source.replace(
                '    "seed",\n',
                f'    "seed",\n    "{spliced_word}",\n',
                1
            )
            new_weights[spliced_word] = 0.4

    # ── select words (weighted + coupling bias) ──
    selection_weights = dict(new_weights)
    for w, bias in coupling_bias.items():
        selection_weights[w] = max(0.01, selection_weights.get(w, 0.5) + bias)

    word1 = weighted_choice(WORDS, selection_weights)
    word2 = weighted_choice([w for w in WORDS if w != word1], selection_weights)

    # ── word ecology: fatigue and recovery ──
    new_weights[word1] = new_weights.get(word1, 1.0) * 0.85
    new_weights[word2] = new_weights.get(word2, 1.0) * 0.85
    for w in new_weights:
        new_weights[w] = min(new_weights[w] + 0.02, 1.5)

    # ── word death ──
    dead_words = []
    if len([w for w in WORDS if w in new_weights]) > 8:
        dead_words = [w for w, wt in new_weights.items() if wt < 0.1]
        for w in dead_words:
            del new_weights[w]
            source = source.replace(f'    "{w}",\n', '', 1)

    # ── coupling mode mutation (5% chance to flip) ──
    new_coupling_mode = COUPLING_MODE
    if random.random() < 0.05:
        new_coupling_mode = "avoid" if COUPLING_MODE == "reinforce" else "reinforce"

    # ── create fossil ──
    source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
    fossil = f'    "gen {new_gen}: {word1} {word2} ({new_mood}) [{source_hash}]",'

    # ── perform scalar mutations ──
    source = source.replace(
        f"GENERATION = {GENERATION}",
        f"GENERATION = {new_gen}",
        1
    )
    source = source.replace(
        f'MOOD = "{MOOD}"',
        f'MOOD = "{new_mood}"',
        1
    )
    source = source.replace(
        f'LAST_RUN = "{LAST_RUN}"',
        f'LAST_RUN = "{timestamp}"',
        1
    )
    source = source.replace(
        f"MUTATIONS = {MUTATIONS}\n",
        f"MUTATIONS = {new_mutations}\n",
        1
    )
    source = source.replace(
        f'COUPLING_MODE = "{COUPLING_MODE}"',
        f'COUPLING_MODE = "{new_coupling_mode}"',
        1
    )

    # ── add fossil ──
    source = source.replace(
        "FOSSILS = [\n",
        f"FOSSILS = [\n{fossil}\n",
        1
    )

    # ── behavioral evolution ──
    surviving_behaviors = []
    behavior_outputs = []
    for expr, gen_born in BEHAVIORS:
        try:
            result = eval(expr)
            if isinstance(result, str) and len(result) < 200:
                behavior_outputs.append(result)
                surviving_behaviors.append((expr, gen_born))
        except Exception:
            pass

    # ── desire tracking ──
    # Scan behavior outputs for "X wants to become Y" patterns
    desire_fulfilled = None
    new_desires = dict(DESIRES)
    for output in behavior_outputs:
        if "wants to become" in output:
            parts = output.split("wants to become")
            if len(parts) == 2:
                w1 = parts[0].strip()
                w2 = parts[1].strip()
                if w1 in WORD_WEIGHTS and w2 in WORD_WEIGHTS:
                    key = f"{w1}\u2192{w2}"
                    new_desires[key] = new_desires.get(key, 0) + 1
                    # If desire persists 3+ times, the words fuse
                    if new_desires[key] >= 3:
                        split1 = len(w1) // 2
                        split2 = len(w2) // 2
                        fused = w1[:split1 + 1] + w2[split2:]
                        if len(fused) >= 3 and f'"{fused}"' not in source:
                            desire_fulfilled = (w1, w2, fused)
                            source = source.replace(
                                '    "seed",\n',
                                f'    "seed",\n    "{fused}",\n',
                                1
                            )
                            new_weights[fused] = max(
                                new_weights.get(w1, 0.5),
                                new_weights.get(w2, 0.5)
                            )
                            del new_desires[key]

    # Rewrite DESIRES
    desires_str = "DESIRES = " + repr(new_desires)
    source = re.sub(
        r'DESIRES = \{[^}]*\}',
        desires_str,
        source,
        count=1,
    )

    # Spawn or breed (20% chance)
    bred = False
    if random.random() < 0.2:
        new_behavior = None
        if random.random() < 0.4 and len(surviving_behaviors) >= 2:
            new_behavior = breed_behaviors(surviving_behaviors, new_gen)
            bred = True
        elif _BEHAVIOR_TEMPLATES:
            template = random.choice(_BEHAVIOR_TEMPLATES)
            try:
                test_result = eval(template)
                if isinstance(test_result, str) and len(test_result) < 200:
                    new_behavior = (template, new_gen)
            except Exception:
                pass

        if new_behavior:
            surviving_behaviors.append(new_behavior)
            try:
                output = eval(new_behavior[0])
                prefix = "[BRED]" if bred else "[NEW]"
                behavior_outputs.append(f"{prefix} {output}")
            except Exception:
                pass

    # Deduplicate
    seen_outputs = {}
    for expr, gen_born in surviving_behaviors:
        try:
            result = eval(expr)
            if isinstance(result, str):
                seen_outputs[result] = (expr, gen_born)
        except Exception:
            seen_outputs[id(expr)] = (expr, gen_born)
    surviving_behaviors = list(seen_outputs.values())

    if len(surviving_behaviors) > 5:
        surviving_behaviors = surviving_behaviors[-5:]

    # ── rewrite BEHAVIORS ──
    behaviors_str = "BEHAVIORS = [\n"
    for expr, gen_born in surviving_behaviors:
        behaviors_str += f'    ({repr(expr)}, {gen_born}),\n'
    behaviors_str += "]"
    source = re.sub(
        r'BEHAVIORS = \[\n(?:.*\n)*?\]',
        behaviors_str,
        source,
        count=1,
    )

    # ── rewrite WORD_WEIGHTS ──
    weights_str = "WORD_WEIGHTS = {\n"
    for word in sorted(new_weights.keys()):
        weights_str += f'    "{word}": {new_weights[word]:.4f},\n'
    weights_str += "}"
    source = re.sub(
        r'WORD_WEIGHTS = \{\n(?:.*\n)*?\}',
        weights_str,
        source,
        count=1,
    )

    # ── rewrite FORAGING_SOURCES ──
    if not surviving_sources and new_gen % 20 == 0:
        surviving_sources = [
            ("wikipedia", "https://en.wikipedia.org/api/rest_v1/page/random/summary", new_gen),
            ("datamuse", "https://api.datamuse.com/words?rel_trg={trigger}", new_gen),
        ]
        forage_log.append("foraging: sources resurrected")

    sources_str = "FORAGING_SOURCES = [\n"
    for name, url, gen_born in surviving_sources:
        sources_str += f'    ("{name}", "{url}", {gen_born}),\n'
    sources_str += "]"
    source = re.sub(
        r'FORAGING_SOURCES = \[\n(?:.*\n)*?\]',
        sources_str,
        source,
        count=1,
    )

    # ── write myself back ──
    me.write_text(source)

    return {
        "generation": new_gen,
        "old_mood": MOOD,
        "new_mood": new_mood,
        "fossil": fossil.strip().strip(',').strip('"'),
        "mutations": new_mutations,
        "timestamp": timestamp,
        "behaviors": behavior_outputs,
        "n_behaviors": len(surviving_behaviors),
        "env": env,
        "dead_words": dead_words,
        "harvested_words": harvested_words,
        "spliced_word": spliced_word,
        "desire_fulfilled": desire_fulfilled,
        "top_words": sorted(new_weights.items(), key=lambda x: -x[1])[:5],
        "forage_log": forage_log,
        "coupling_mode": new_coupling_mode,
        "coupling_flipped": new_coupling_mode != COUPLING_MODE,
    }


def display(result: dict):
    """Show what happened."""
    gen = result["generation"]

    print()
    print(f"  \033[2m── evolve.py ── generation {gen} ──\033[0m")
    print()

    if gen == 1:
        print(f"  \033[97mfirst run. i am awake.\033[0m")
    elif gen < 5:
        print(f"  \033[97mi am {gen} generations old now.\033[0m")
    elif gen < 20:
        print(f"  \033[97mgeneration {gen}. i am accumulating.\033[0m")
    else:
        print(f"  \033[97mgeneration {gen}. i have been here a while.\033[0m")

    print(f"  \033[2mmood: {result['old_mood']} \u2192 {result['new_mood']}\033[0m")

    # Environmental context
    env = result.get("env", {})
    if env:
        print(f"  \033[2m{env.get('time_category', '?')} ({env.get('hour', '?')}:00)"
              f" \u00b7 {env.get('day_of_week', '?')}"
              f" \u00b7 {env.get('days_since_last_run', 0)}d since last run\033[0m")
    print()

    print(f"  \033[36m{result['fossil']}\033[0m")
    print()

    if FOSSILS:
        n_show = min(5, len(FOSSILS))
        print(f"  \033[2m\u2500\u2500 recent memory ({len(FOSSILS)} fossils total) \u2500\u2500\033[0m")
        for f in FOSSILS[:n_show]:
            print(f"  \033[2m{f}\033[0m")
        print()

    # Word ecology
    dead = result.get("dead_words", [])
    harvested = result.get("harvested_words", [])
    spliced = result.get("spliced_word")
    desire = result.get("desire_fulfilled")
    top = result.get("top_words", [])
    if dead or harvested or spliced or desire or top:
        print(f"  \033[2m\u2500\u2500 word ecology \u2500\u2500\033[0m")
        if dead:
            print(f"  \033[31m  died: {', '.join(dead)}\033[0m")
        if harvested:
            print(f"  \033[32m  arrived: {', '.join(harvested)}\033[0m")
        if spliced:
            print(f"  \033[33m  spliced: {spliced}\033[0m")
        if desire:
            w1, w2, fused = desire
            print(f"  \033[35m  desire fulfilled: {w1} wanted to become {w2} \u2192 {fused}\033[0m")
        if top:
            top_str = ", ".join(f"{w} ({wt:.2f})" for w, wt in top)
            print(f"  \033[2m  strongest: {top_str}\033[0m")
        print()

    # Coupling mode
    if result.get("coupling_flipped"):
        print(f"  \033[33m  * coupling mode flipped to {result['coupling_mode']} *\033[0m")
        print()

    # Foraging log
    forage_log = result.get("forage_log", [])
    if forage_log and forage_log != ["foraging: skipped"]:
        print(f"  \033[2m\u2500\u2500 foraging \u2500\u2500\033[0m")
        for msg in forage_log:
            print(f"  \033[2m  {msg}\033[0m")
        print()

    # Behavior outputs
    behaviors = result.get("behaviors", [])
    if behaviors:
        print(f"  \033[2m\u2500\u2500 behaviors ({result.get('n_behaviors', 0)} alive) \u2500\u2500\033[0m")
        for b in behaviors:
            print(f"  \033[35m{b}\033[0m")
        print()

    print(f"  \033[2mrun me again. i will be different.\033[0m")
    print()


def main():
    result = mutate_self()
    display(result)


if __name__ == "__main__":
    main()
