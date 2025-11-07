#!/usr/bin/env python3
"""Combine two song's pdfs on the same page. Use this for short songs."""

import os
import shutil
import subprocess

from songbook_maker.song_index import VARIANT_SUFFIXES


def song_path(song, suffix):
    """Get full path to the song's pdf file."""
    song_name = song["name"]
    song_number = song["number"]
    return f"./static/songs/{song_name}/{song_number}_{song_name}{suffix}.pdf"


def combine(top_song, bottom_song, offset=400):
    """Combine the two songs' pdfs and overwrite them both."""
    for suffix in VARIANT_SUFFIXES:
        top_path = song_path(top_song, suffix)
        bottom_path = song_path(bottom_song, suffix)
        subprocess.run(
            [
                "cpdf",
                "-shift",
                f"0 -{offset}",
                bottom_path,
                "-o",
                "bottom_song_shifted.pdf",
            ],
            check=True,
        )
        subprocess.run(
            [
                "pdftk",
                top_path,
                "background",
                "bottom_song_shifted.pdf",
                "output",
                "combined.pdf",
            ],
            check=True,
        )
        shutil.move("combined.pdf", top_path)
        shutil.copy(top_path, bottom_path)
        os.remove("bottom_song_shifted.pdf")
