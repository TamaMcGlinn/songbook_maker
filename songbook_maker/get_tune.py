#!/usr/bin/env python3
"""Extract a tune from a MuseScore 4-part harmony."""

import errno
import os
import shutil
import subprocess
import sys

import music21

from songbook_maker.export_songs import export_job
from songbook_maker.musicxml_to_solfege import musicxml_to_solfege
from songbook_maker.song_index import VOICES


def export_one_part_xml(musescore_file, desired_part):
    file_dir, file_name = os.path.split(musescore_file)
    file_base_name = file_name.rsplit(".", 1)[0]
    out_definition = []
    out_definition.append(f'["{file_base_name}-", ".xml"]')
    out_definition_string = ",".join(out_definition)
    job = (
        "["
        "  {"
        f'    "in": "{musescore_file}",'
        f'    "out": [{out_definition_string}]'
        "  }"
        "]"
    )
    export_job(job)

    for part in VOICES:
        if part == desired_part:
            continue  # keep this one
        os.remove(f"{file_base_name}-{part}.xml")
    return f"{file_base_name}-{desired_part}.xml"


def get_tune(musescore_file, desired_part):
    part_xml = export_one_part_xml(musescore_file, desired_part)
    # now we have e.g. some_song-Soprano.xml
    tune = musicxml_to_solfege(part_xml, None)
    os.remove(part_xml)
    return tune


if __name__ == "__main__":
    tune = get_tune(sys.argv[1], "Soprano")
    print(tune)
