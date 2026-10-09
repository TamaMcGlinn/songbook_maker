#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

from export_songs import export_lyrics, find_musescore_files, replace_extension
from openai import OpenAI
from song_index import read_title, uptodate_from_source

MODEL = "gpt-5-mini"

CATEGORIES = [
    "Praise and Worship",
    "Thanksgiving",
    "Prayer and Supplication",
    "Faith and Trust",
    "Grace and Salvation",
    "Repentance and Forgiveness",
    "Christmas",
    "Resurrection",
    "Holy Spirit",
    "Church and Fellowship",
    "Mission and Service",
    "Hope and Eternal Life",
]


def classify_hymn(title, lyrics, categories=None):
    client = OpenAI()

    if categories is None:
        category_lines = "\n".join(CATEGORIES)
        category_instruction = f"\n\nChoose a category such as:\n{category_lines}\n\n"
        category_instruction += "The category name should be in the same language as "
        category_instruction += "the song title and lyrics."
    else:
        category_lines = "\n".join(categories)
        category_instruction = f"\n\nChoose a category from:\n{category_lines}\n\n"
    response = client.responses.create(
        model=MODEL,
        instructions=(
            "You are an expert in Christian hymnology. "
            "Classify hymns according to their primary "
            "theological or liturgical theme."
            + category_instruction
            + "Consider both the title and lyrics. "
            "Give greater weight to the lyrics. "
            "Return ONLY the category name, without "
            "explanations or additional text."
        ),
        input=f"Title:\n{title}\n\nLyrics:\n{lyrics}",
    )

    return response.output_text.strip()

def categorize(musescore_file):
    lyrics_filename = replace_extension(musescore_file, ".txt")
    if not uptodate_from_source(lyrics_filename, musescore_file):
        export_lyrics(musescore_file)
    lyrics = Path(lyrics_filename).read_text(encoding="utf-8").strip()
    title = read_title(musescore_file)
    return classify_hymn(title, lyrics)


def read_categories(category_file):
    with open(category_file, "r", encoding="utf-8") as file:
        category_contents = file.read()
    return read_back_values(category_contents)


def read_back_values(value_str):
    lines = value_str.strip().split('\n')
    categories = {}
    for line in lines:
        key, values = line.split(': ')
        categories[key] = values.split()
    return categories


def get_category(categories: dict, song_id: str):
    """Retrieve the song_id's category from the given dict."""
    for category, song_list in categories.items():
        if song_id in song_list:
            return category
    return None


def count_songs(categories: dict):
    """Count the number of songs in the categories dict."""
    return sum(len(values) for values in categories.values())


def main() -> None:
    """Categorize any missing songs in the given directory."""
    parser = argparse.ArgumentParser(
        description="Determine the hymn's category."
    )
    help_txt = "Path containing MusicXML .mscx files, each bundled with lyrics txt."
    parser.add_argument("target_dir", help=help_txt)
    args = parser.parse_args()
    musescore_files = find_musescore_files(args.target_dir)
    category_file = Path(args.target_dir) / "categories.txt"
    if os.path.isfile(category_file):
        categories = read_categories(category_file)
        print(f"Read existing {category_file} with {count_songs(categories)} songs classified.")
    else:
        categories = {}
    categorized_something_new = False
    for file in musescore_files:
        song_id = Path(file).stem
        category = get_category(categories, song_id)
        if category is not None:
            continue
        print(f"Analyzing song text and title for {song_id} to determine category...")
        category = categorize(file)
        print(f"{song_id} added to category: {category}")
        categorized_something_new = True
        if category in categories:
            categories[category].append(song_id)
        else:
            categories[category] = [song_id]
    if categorized_something_new:
        print(f"Writing {category_file} with {count_songs(categories)} songs classified.")
        lines = [f"{key}: {' '.join(value)}" for key, value in categories.items()]
        category_file.write_text('\n'.join(lines))
    else:
        print("All songs were already categorized.")


if __name__ == "__main__":
    main()
