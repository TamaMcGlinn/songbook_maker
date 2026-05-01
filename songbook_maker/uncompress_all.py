#!/usr/bin/env python3
"""Replace MS4 mscz files with uncompressed mscx files."""

import errno
import os
import shutil
import subprocess
import sys

MUSESCORE_BINARY = "/usr/bin/musescore4"


def export(musescore_file, extension, master, parts):
    """Export the given musescore file (audio / lyrics, etc)."""
    file_dir, file_name = os.path.split(musescore_file)
    file_base_name = file_name.rsplit(".", 1)[0]
    out_definition = []
    if master:
        out_definition.append(f'"{file_dir}/{file_base_name}{extension}"')
    if parts:
        out_definition.append(f'["{file_dir}/{file_base_name}-", "{extension}"]')
    out_definition_string = ",".join(out_definition)
    job = (
        "["
        "  {"
        f'    "in": "{musescore_file}",'
        f'    "out": [{out_definition_string}]'
        "  }"
        "]"
    )
    with open("job.json", "w", encoding="utf-8") as jobfile:
        jobfile.write(job)
    subprocess.check_output(
        [MUSESCORE_BINARY, "-j", "job.json"], stderr=subprocess.DEVNULL
    )
    os.remove("job.json")


def export_uncompressed(musescore_file):
    """Export from musescore to file adjacent with uncompressed musescore filename."""
    export(musescore_file, ".mscx", True, False)


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


def silentremove(filename):
    """Remove file if it exists."""
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


def silentrmtree(foldername):
    """Remove folder if it exists."""
    try:
        shutil.rmtree(foldername)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


silentremove("audiosettings.json")
silentremove("score_style.mss")
silentremove("viewsettings.json")
silentrmtree("META-INF")
silentrmtree("Thumbnails")
