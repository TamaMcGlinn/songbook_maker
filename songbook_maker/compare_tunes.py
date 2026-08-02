#!/usr/bin/env python3
"""Compare the tunes of pairs of files, or a directory of MuseScore files."""

import os
import sys

from songbook_maker.get_tune import get_tune


def get_duplicate_tunes(files, voice):
    tune_song_index = {}
    for file in files:
        tune = str(get_tune(file, voice))
        prior_song_same_tune = tune_song_index.get(tune, None)
        if prior_song_same_tune:
            # add this file to list of songs with that tune
            prior_song_same_tune.append(file)
        else:
            # make new list with just this file
            tune_song_index[tune] = [file]
    duplicate_tunes = {k: v for k, v in tune_song_index.items() if len(v) > 1}
    return duplicate_tunes


def compare(files):
    duplicate_sopranos = get_duplicate_tunes(files, "Soprano")
    print(duplicate_sopranos)


def arg_help():
    print("Usage: compare_tunes.py [file | directory]*")
    print("e.g. compare_tunes.py file1.mscx file2.mscx")
    print("or   compare_tunes.py english/ file2.mscx")


def muse_score_files_in(path_to_dir):
    file_paths = []
    for root, _, files in os.walk(path_to_dir):
        for file in files:
            if file.endswith(".mscx"):
                file_paths.append(os.path.join(root, file))
    return file_paths


if __name__ == "__main__":
    file_paths = []
    for arg in sys.argv[1:]:
        if arg == "--help":
            print_help()
            sys.exit(0)
        if os.path.isfile(arg):
            file_paths.append(arg)
        elif os.path.isdir(arg):
            file_paths += muse_score_files_in(arg)
        else:
            raise RuntimeError(f"{arg} is not a valid file or directory.")
    compare(file_paths)
