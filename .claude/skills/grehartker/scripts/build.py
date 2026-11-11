"""Génère build/grehartker.ttf à partir de src/grehartker.sfd.

Usage (avec le Python de FontForge) :
    ffpython S/build.py src/grehartker.sfd build/grehartker.ttf
"""
import sys

import fontforge

f = fontforge.open(sys.argv[1])
f.generate(sys.argv[2], flags=("opentype",), layer="Fore")
print("généré :", sys.argv[2])
