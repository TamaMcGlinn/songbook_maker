#!/usr/bin/env python3
"""Generate index of given songs in both PDF and HTML.

HTML page allows playing the different parts at variable volume.
The page links to the PDFs for each song individually and also
to the master pdf files, containing all the songs (for 2 variants).
"""

import bisect
import os
import re
import subprocess
import unicodedata
from collections import namedtuple

from songbook_maker.export_songs import (export_audio, export_lyrics,
                                         export_pdf, export_pdf_round,
                                         replace_extension)

# directory containing all songs; TODO pass this in instead
SONG_INDEX = "./static/songs/"

# the song index directory may also contain shared_melodies.txt,
# the first element has audio exported, others share them
SHARED_MELODIES = {}

VOICES = ["Soprano", "Alto", "Tenor", "Bass"]

VARIANT_SUFFIXES = ["", "_rond"]

PREAMBLE = """
<!DOCTYPE html>
<html>
  <head>
    <script src="/js/play_satb.js"></script>
    <script src="/js/remember_settings.js"></script>
    <link rel="stylesheet" type="text/css" href="/css/songpage.css">
    <script>
"""
END_HEADER = """
    </script>
  </head>
<body>
"""
SLIDERS_TABLE = """
<table id="tbl_volume">
  <tr>
      <th><input type="range" min="0" max="100" class="volume_slider" orient="vertical" onchange="volume_change()" id="sld_volume" /></th>
      <th><input type="range" min="0" max="100" class="volume_slider" orient="vertical" onchange="slider_change('Soprano')" id="sld_Soprano" /></th>
      <th><input type="range" min="0" max="100" class="volume_slider" orient="vertical" onchange="slider_change('Alto')" id="sld_Alto" /></th>
      <th><input type="range" min="0" max="100" class="volume_slider" orient="vertical" onchange="slider_change('Tenor')" id="sld_Tenor" /></th>
      <th><input type="range" min="0" max="100" class="volume_slider" orient="vertical" onchange="slider_change('Bass')" id="sld_Bass" /></th>
  </tr>
  <tr>
      <th>All</th>
      <th>Soprano</th>
      <th>Alto</th>
      <th>Tenor</th>
      <th>Bass</th>
  </tr>
</table>
Tempo: <input type="range" min="20" max="400" step="5" class="speed_slider" orient="horizontal" value="100" onchange="speed_slider_change()" id="sld_speed" /><label id="lbl_speed" for="sld_speed">1x</label>
<button text="reset " onclick="reset_speed()">Reset</button>
<br/>
"""
TABLE_START = """
<br/>
<table id="tbl_allparts">
"""
POSTFIX = """
</table>

</body>
</html>
"""


def number_sequentially(songlist):
    songs = []
    i = 1
    for song in songlist:
        songs.append({"name": song, "number": str(i)})
        i += 1
    return songs


def link_master_file(file, index_dir):
    """Write table line for the master PDF's to file (html)."""
    master_pdf_link_dir = index_dir.removeprefix("./static")
    file.write("<div id='div_allsongs'>")
    file.write("<label id='lbl_allsongs'>All songs / Alle liederen: </label>")
    file.write(
        f"<td><a href='{master_pdf_link_dir}/all_rond.pdf'"
        "target='_blank'><img src='/images/roundnote.png'"
        "class='music_open'></a></td>"
    )
    file.write(
        f"<td><a href='{master_pdf_link_dir}/all.pdf'"
        "target='_blank'><img src='/images/shapenote.png'"
        "class='music_open'></a></td>"
    )
    file.write("</div>")


def read_song_collection_properties():
    """Read shared_melodies.txt to a dictionary for lookup.

    The first song on each line is the melody song, others
    are stored in the dictionary and reference the melody song.
    """
    global SHARED_MELODIES
    SHARED_MELODIES = {}
    shared_melodies_filename = f"{SONG_INDEX}shared_melodies.txt"
    if not os.path.isfile(shared_melodies_filename):
        # No shared melodies; that's fine, use empty dictionary
        return
    with open(shared_melodies_filename, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("#"):
                continue
            titles = line.split()
            first = titles[0]
            for duplicate in titles[1:]:
                # print(f"{duplicate} has shared melody with {first}")
                SHARED_MELODIES[duplicate] = first


def get_song_id(song):
    """Get path in static/ to song, it's the {language}/{name}."""
    return f"{song['language']}/{song['name']}"


def convert_song_id_for_html(song_id):
    """Get {language}_{name} for song, for use as id inside HTML."""
    return song_id.replace("/", "_")  # because HTML id cannot contain /


def get_melody(song_id):
    """Return melody song id, which is language/song_name.

    Usually it just returns song_id unchanged, but for shared melodies
    it returns the source song id.
    """
    # change the src if song name in SHARED_MELODIES
    return SHARED_MELODIES.get(song_id, song_id)


def get_audio_src(song_id, voice):
    """Return relative mp3 file path for given song and voice."""
    melody = get_melody(song_id)
    _, song_name = melody.split("/")
    return f"/songs/{melody}/{song_name}-{voice}.mp3"


def get_musescorefile(song_id):
    """Return relative musescore file for song."""
    _, song_name = song_id.split("/")
    return f"{SONG_INDEX}{song_id}/{song_name}.mscx"


def get_melody_musescorefile(song):
    """Return melody musescore file.

    Usually it's the same as the song_name.mscx, but for shared melodies
    it points to the source musescore file.
    """
    song_id = get_song_id(song)
    melody = get_melody(song_id)
    return get_musescorefile(melody)


def write_audio(file, song, voice):
    """Write html for audio element pointing to specific voice of song to file."""
    song_id = get_song_id(song)
    html_song_id = convert_song_id_for_html(song_id)
    audio_song_id = get_melody(song_id)
    html_audio_song_id = convert_song_id_for_html(audio_song_id)
    file.write(f'<audio id="{html_song_id}-{voice}" loop=true>\n')
    audio_src = get_audio_src(song_id, voice)
    file.write(f'  <source src="{audio_src}" type="audio/mpeg">\n')
    file.write("  Your browser does not support the audio element.\n")
    file.write("</audio>\n")


def prettify_name(song_name):
    """Reconstruct song name from filename.

    The filename cannot contain punctuation,
    nor does it have the correct capitalization.
    """
    song_name = song_name.capitalize()
    song_name = re.sub(r"_(\w)", lambda x: " " + x.group(1).upper(), song_name)
    song_name = (
        song_name.replace("I Ll", "I'll").replace("We Ll", "We'll").replace("T ", "'t ")
    )
    return song_name


def prettify_and_shorten_name(song_name):
    """Shorten and prettify name to fit in HTML title element."""
    song_name = prettify_name(song_name)
    if len(song_name) > 20:
        song_name = song_name[:19] + "…"
    return song_name


def write_song_to_html(file, song):
    """Write all needed elements for the given song to html file."""
    name = song["name"]
    song_id = get_song_id(song)
    html_song_id = song_id.replace("/", "_")
    number = song["number"]
    file.write("  <tr>\n")
    file.write(
        f'    <td><button onclick="resetSong({html_song_id})" type="button"'
        'class="mediabutton">⏮</button></td>\n'
    )
    file.write("    <td>\n")
    file.write("      <table>\n")
    file.write("        <tr><td>\n")
    file.write(f"          <span>{number} {prettify_and_shorten_name(name)}</span>\n")
    file.write("        </td></tr>\n")
    file.write("        <tr><td>\n")
    file.write(
        f'          <progress id="pgb_{html_song_id}" value="0" max="100" '
        'class="music_progress"></progress>\n'
    )
    file.write("        </td></tr>\n")
    file.write("      </table>\n")
    file.write("    </td>\n")
    file.write(
        f'    <td><button onclick="playPause({html_song_id})"'
        'type="button" class="mediabutton">⏯ </button></td>\n'
    )
    rond_pdf = f"/songs/{song_id}/{number}_{name}_rond.pdf"
    shapenote_pdf = f"/songs/{song_id}/{number}_{name}.pdf"
    source_mscx = f"/songs/{song_id}/{name}.mscx"
    file.write(
        f"    <td><a href='{rond_pdf}' "
        "target='_blank'><img src='/images/roundnote.png' class='music_open'></a></td>\n"
    )
    file.write(
        f"    <td><a href='{shapenote_pdf}' "
        "target='_blank'><img src='/images/shapenote.png' class='music_open'></a></td>\n"
    )
    file.write(
        f"    <td><a href='{source_mscx}' "
        "target='_blank'><img src='/images/mscore_dl.png' class='music_open'></a></td>\n"
    )
    file.write("  </tr>\n")


def uptodate_from_source(product_file, source_file):
    """Check if given product file, produced from source (.mscx) is up to date.

    Returns whether the productfile exists and is newer than source_file.
    """
    if not os.path.isfile(product_file):
        return False
    if not os.path.isfile(source_file):
        print(f"Error: missing source file {source_file}\n")
        return False
    productfile_written = os.path.getmtime(product_file)
    sourcefile_written = os.path.getmtime(source_file)
    return productfile_written > sourcefile_written


def all_voices_uptodate(song, musescore_file):
    """Return whether all voices audio files are present and up to date."""
    for voice in VOICES:
        song_id = get_melody(get_song_id(song))
        audio_src = get_audio_src(song_id, voice)
        file_path = f"./static{audio_src}"
        if not uptodate_from_source(file_path, musescore_file):
            return False
    return True


def unnumbered_rond_pdf_file_uptodate(musescore_file):
    """Return true iff round-note unnumbered pdf up to date."""
    pdf_filename = replace_extension(musescore_file, "_rond.pdf")
    return uptodate_from_source(pdf_filename, musescore_file)


def unnumbered_pdf_file_uptodate(musescore_file):
    """Return true iff unnumbered pdf up to date."""
    pdf_filename = replace_extension(musescore_file, ".pdf")
    return uptodate_from_source(pdf_filename, musescore_file)


def lyrics_file_uptodate(musescore_file):
    """Return true iff lyrics up to date.

    .txt file adjacent must be present
    and newer than the musescore file.
    """
    lyrics_filename = replace_extension(musescore_file, ".txt")
    return uptodate_from_source(lyrics_filename, musescore_file)


def export_missing_pdfs(s):
    """Generate pdfs where missing."""
    for song in s:
        musescore_file = get_musescorefile(get_song_id(song))
        if not unnumbered_pdf_file_uptodate(musescore_file):
            print(f"Generating pdf from {musescore_file}")
            export_pdf(musescore_file)
        if not unnumbered_rond_pdf_file_uptodate(musescore_file):
            print(f"Generating roundnote pdf from {musescore_file}")
            export_pdf_round(musescore_file)


def export_missing_audio(s):
    """Generate audio where missing."""
    for song in s:
        musescore_file = get_musescorefile(get_song_id(song))
        if not lyrics_file_uptodate(musescore_file):
            print(f"Extracting lyrics from {musescore_file}")
            export_lyrics(musescore_file)
        melody_musescore_file = get_melody_musescorefile(song)
        if not all_voices_uptodate(song, melody_musescore_file):
            print(f"Exporting audio from {melody_musescore_file}")
            export_audio(melody_musescore_file)


def get_lyrics(musescore_file):
    """Get lyrics lines from musescore file."""
    lyrics_filename = replace_extension(musescore_file, ".txt")
    with open(lyrics_filename, "r", encoding="utf-8") as file:
        return file.read()


def remove_leading_numbers_and_spaces(lyrics: str):
    """Remove leading numbers and spaces."""
    return lyrics.lstrip("1234567890. ").lstrip()


def get_first_line_of_lyrics(song):
    """Get first line of lyrics for the song."""
    song_id = get_song_id(song)
    musescore_file = get_musescorefile(song_id)
    lyrics = remove_leading_numbers_and_spaces(get_lyrics(musescore_file))
    return get_first_line_of(lyrics)


def get_first_line_of(lyrics):
    """Find the first line of the lyrics."""
    min_firstline = 20
    max_firstline = 40
    # search backwards from max to min for punctuation
    for i in range(max_firstline, min_firstline, -1):
        if lyrics[i] in [".", ",", ";", ":", "!", "?"]:
            return lyrics[: i + 1]
    words = lyrics[:max_firstline].split()
    result = " ".join(words[:-1]) if len(words) > 1 else words[0][:max_firstline]
    return result


def remove_punctuation(text):
    """Remove punctuation."""
    punctuation = [".", ",", ";", ":", "!", "?", "'"]
    for char in punctuation:
        text = text.replace(char, " ").replace("  ", " ")
    return text


def replace_nonascii(text):
    """Replace non-ascii chars from text."""
    # Normalize to decomposed form (e.g., ê → e + ˆ)
    normalized = unicodedata.normalize("NFD", text)
    # Remove all combining characters (accents, diacritics, etc.)
    ascii_only = "".join(char for char in normalized if not unicodedata.combining(char))
    return ascii_only


IndexEntry = namedtuple("IndexEntry", ("entry", "number"))


def sanitize_for_comparison(text):
    """Return the text in normalized form to compare."""
    return (
        replace_nonascii(remove_punctuation(text.lower()))
        .replace(
            "prayr",
            "prayer",  # make pray'r in lyrics equivalent to prayer in title
        )
        .replace(" ", " ")
    )  # replace non-breaking spaces with regular


def get_index_of_titles_and_first_lines(songlist):
    """Get list of titles or first lines, paired with song number."""
    index = []
    for song in songlist:
        prettified_name = prettify_name(song["name"])
        song_number = song["number"]
        entry = IndexEntry(prettified_name, song_number)
        bisect.insort(index, entry, key=lambda x: sanitize_for_comparison(x.entry))
        first_line = get_first_line_of_lyrics(song)
        # if the first line is basically just the title (barring capitalization & punctuation),
        # we skip the first line entry, and only have the title
        # so that we don't get, for example, both these:
        # Wie K In Nachtegael                       2363
        # Wie'k in nachtegael dan soe ik            2363
        comparing_first_line = sanitize_for_comparison(first_line)
        comparing_title = sanitize_for_comparison(prettified_name)
        if not comparing_first_line.startswith(comparing_title):
            line_entry = IndexEntry(first_line, song_number)
            bisect.insort(index, line_entry, key=lambda x: x.entry)
    return index


def apply_language(songs, new_language):
    """Set language for all songs."""
    for s in songs:
        s["language"] = new_language


def generate_index(songs, index_path, language=None, frontpage_dir=None):
    """Generate index html and pdf.

    also ensure no generated files are missing.
    """
    if language:
        apply_language(songs, language)
    read_song_collection_properties()
    export_missing_pdfs(songs)
    number_songs(songs)
    export_missing_audio(songs)
    index_dir, _ = os.path.split(index_path)
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)
    create_master_pdfs(songs, index_dir, frontpage_dir)
    with open(index_path, "w", encoding="utf-8") as file:
        file.write(PREAMBLE)
        songs = sorted(songs, key=lambda x: int(re.search(r"\d+", x["number"]).group()))
        for song in songs:
            song_id = convert_song_id_for_html(get_song_id(song))
            file.write(f'const {song_id} = {{name: "{song_id}"}}\n')
        song_ids = ",".join([convert_song_id_for_html(get_song_id(s)) for s in songs])
        file.write(f"const songs = [{song_ids}]")
        file.write(END_HEADER)
        for song in songs:
            for voice in VOICES:
                write_audio(file, song, voice)
        file.write(SLIDERS_TABLE)
        link_master_file(file, index_dir)
        file.write(TABLE_START)
        for song in songs:
            write_song_to_html(file, song)
        file.write(POSTFIX)


def number_songs(s):
    """Generate numbered pdfs where they are missing or not up to date."""
    for song in s:
        name = song["name"]
        song_id = get_song_id(song)
        number = song["number"]
        for suffix in VARIANT_SUFFIXES:
            numbered_file = f"{SONG_INDEX}{song_id}/{number}_{name}{suffix}.pdf"
            unnumbered_file = f"{SONG_INDEX}{song_id}/{name}{suffix}.pdf"
            if not uptodate_from_source(numbered_file, unnumbered_file):
                if os.path.isfile(unnumbered_file):
                    print(f"Generating {numbered_file}...\n")
                    subprocess.check_output(
                        [
                            "cpdf",
                            "-add-text",
                            str(number),
                            "-topright",
                            "50",
                            "-font",
                            "Helvetica",
                            "-font-size",
                            "26",
                            unnumbered_file,
                            "-o",
                            numbered_file,
                        ]
                    )


def highest_version_in(frontpage_dir, variant):
    """Return the highest versioned pdf frontpage filename."""
    highest_version = None
    for i in range(1, 99):
        edfile = os.path.join(frontpage_dir, f"ed{i}{variant}.pdf")
        if os.path.isfile(edfile):
            highest_version = edfile
    return highest_version


def create_index_page(s):
    """Create index pdf with song titles and first lines."""
    print("===INDEX OF TITLES AND 1ST LINES===")
    index_lines = get_index_of_titles_and_first_lines(s)
    with open("temp_index_page.txt", "w", encoding="utf-8") as file:
        for song in index_lines:
            file.write(f"{song.entry:<42}{str(song.number):>4}\n")
            print(f"{song.entry:<42}{str(song.number):>4}")
    subprocess.check_output(["soffice", "--convert-to", "pdf", "./temp_index_page.txt"])
    os.remove("temp_index_page.txt")
    print("===================================")


def create_master_pdfs(s, index_dir, frontpage_dir):
    """Create both variant master pdfs."""
    create_index_page(s)
    for suffix in VARIANT_SUFFIXES:
        create_master_pdf(s, index_dir, frontpage_dir, suffix)


def create_master_pdf(s, index_dir, frontpage_dir, suffix):
    """Collect the songs' pdfs into an all.pdf and all_rond.pdf."""
    parts = []
    if frontpage_dir:
        frontpage = highest_version_in(frontpage_dir, suffix)
        if not frontpage:
            frontpage = highest_version_in(frontpage_dir, "")
        if frontpage:
            parts.append(frontpage)
    for song in s:
        name = song["name"]
        number = song["number"]
        song_id = get_song_id(song)
        parts.append(f"{SONG_INDEX}{song_id}/{number}_{name}{suffix}.pdf")
    parts.append("temp_index_page.pdf")
    master_file = os.path.join(index_dir, f"all{suffix}.pdf")
    subprocess.check_output(["pdftk", *parts, "cat", "output", master_file])
