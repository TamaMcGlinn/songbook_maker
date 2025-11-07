#!/usr/bin/env python3

import os
import sys
import xml.etree.ElementTree as ET

from songbook_maker.export_songs import export_uncompressed, replace_extension

search_dir = sys.argv[1] if len(sys.argv) > 1 else "."

mscz_files = [
    os.path.join(root, f)
    for root, dirs, files in os.walk(search_dir)
    for f in files
    if os.path.isfile(os.path.join(root, f)) and f.endswith(".mscz")
]

for mscz_file in mscz_files:
    export_uncompressed(mscz_file)
    os.remove(mscz_file)
