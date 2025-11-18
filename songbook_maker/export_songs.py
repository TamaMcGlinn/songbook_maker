#!/usr/bin/env python3

import os
import re
import subprocess
import sys

MUSESCORE_BINARY = "/snap/bin/musescore.mscore"


def find_musescore_files(songs_path):
    """Return all musescore files in the given dir."""
    songs = []
    for root, _, files in os.walk(songs_path):
        for file in files:
            if file.endswith(".mscx"):
                songs.append(os.path.join(root, file))
    return songs


def run_ffmpeg_and_return_output_duration(command):
    p = subprocess.run(
        command,
        capture_output=True,
        check=True,
    )
    ffmpeg_output = p.stderr.decode().splitlines()
    time = None
    for line in ffmpeg_output:
        match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
        if match:
            time = match.group(1)
            # print(f"Match: {time}!")
    return time


def time_to_array(time):
    """Convert time like 00:01:04.36 to [0, 1, 4, 36]."""
    match = re.search(r"(\d{2}):(\d{2}):(\d{2})\.(\d{2})", time)
    if not match:
        raise RuntimeError(f"Invalid time given: {time}")
    return [match.group(1), match.group(2), match.group(3), match.group(4)]


def time_is_less(other_voice_time, time):
    """Takes two times like 00:01:04.36 and returns True if other_voice_time is less than time."""
    time_a = time_to_array(other_voice_time)
    time_b = time_to_array(time)
    for i in range(0, 4):
        if time_a[i] < time_b[i]:
            return True
        if time_a[i] > time_b[i]:
            return False
    return False


def get_audio_length(file):
    return run_ffmpeg_and_return_output_duration(
        [
            "ffmpeg",
            "-i",
            file,
            "-f",
            "null",
            "-",
        ]
    )


def trim(file_dir, voice_file_base_name, time):
    original_voice_file = f"{file_dir}/{voice_file_base_name}.mp3"
    trimmed_voice_file = f"{file_dir}/{voice_file_base_name}-trimmed.mp3"
    resulting_duration = run_ffmpeg_and_return_output_duration(
        [
            "ffmpeg",
            "-i",
            original_voice_file,
            "-ss",
            "00:00:00",
            "-to",
            f"{time}0",
            "-map_chapters",
            "-1",
            "-avoid_negative_ts",
            "2",
            trimmed_voice_file,
        ]
    )
    os.rename(trimmed_voice_file, original_voice_file)
    # if resulting_duration != time:   # you might not expect this, but it's always the case
    #     print(                       # However, output is consistent so it's good enough
    #         f"Warning; after ffmpeg trim to {time} the time"
    #         f"of the resulting file is {resulting_duration}"
    #     )
    return resulting_duration


def trim_silent_endings(musescore_file):
    """Trim the silent ending of the Soprano, then trim the others to match its length exactly."""
    # print("Trimming " + musescore_file)
    file_dir, file_name = os.path.split(musescore_file)
    file_base_name = file_name.rsplit(".", 1)[0]
    soprano_file = f"{file_dir}/{file_base_name}-Soprano.mp3"
    new_soprano_file = f"{file_dir}/{file_base_name}-Soprano-trimmed.mp3"
    time = run_ffmpeg_and_return_output_duration(
        [
            "ffmpeg",
            "-i",
            soprano_file,
            "-af",
            "silenceremove=stop_periods=-1:stop_duration=0.8:stop_threshold=-30dB",
            new_soprano_file,
        ]
    )
    if not time:
        raise RuntimeError(
            f"Error: unknown length of {new_soprano_file} after trimming silence."
        )
    # print(f"Soprano trimmed time, will apply to all voices: {time}")
    os.rename(new_soprano_file, soprano_file)
    shortest_time = time
    durations = {"Soprano": None, "Alto": None, "Tenor": None, "Bass": None}
    for other_voice in ["Soprano", "Alto", "Tenor", "Bass"]:
        voice_file_base_name = f"{file_base_name}-{other_voice}"
        other_voice_time = trim(file_dir, voice_file_base_name, time)
        # print(f"{other_voice} trimmed to {other_voice_time}")
        durations[other_voice] = other_voice_time
        if time_is_less(other_voice_time, shortest_time):
            # print(f"New time {other_voice_time} is less than {shortest_time}.")
            shortest_time = other_voice_time
    # print(f"Shortest time: {shortest_time}.")

    # final double-check; they should all be the same length now
    first_time = None
    for voice in ["Soprano", "Alto", "Tenor", "Bass"]:
        voice_file_name = f"{file_dir}/{file_base_name}-{voice}.mp3"
        voice_time = get_audio_length(voice_file_name)
        if first_time is None:
            first_time = voice_time
        else:
            if voice_time != first_time:
                # Note if this happens, another idea is to append silence to the shorter files with:
                # "apad=pad_dur=1" where 1 is replaced with the length of time to add
                pass
                # raise RuntimeError(
                #     f"Unable to get all voices of {file_base_name} the same length, {voice_file_name} is {voice_time} but Soprano is {first_time}"
                # )


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


def export_pdf(musescore_file):
    """Write pdf from musescore to file adjacent named .pdf"""
    export(musescore_file, ".pdf", True, False)


def export_pdf_round(musescore_file):
    """Write round note pdf from musescore, removing noteheadScheme first."""
    round_file = replace_extension(musescore_file, "_rond.mscx")
    # remove lines like:
    # <noteheadScheme>shape-7-aikin</noteheadScheme>
    #     <headScheme>shape-7-aikin</headScheme>
    pattern = re.compile(r"<(note)?headScheme>shape-7-aikin</(note)?headScheme>")
    with open(musescore_file, "r", encoding="utf8") as input_file, open(
        round_file, "w", encoding="utf8"
    ) as output_file:
        for line in input_file:
            if not pattern.search(line):
                output_file.write(line)
    export(round_file, ".pdf", True, False)
    os.remove(round_file)


def export_audio(musescore_file):
    """Create audio files, trimmed to be the same length."""
    export(musescore_file, ".mp3", False, True)
    trim_silent_endings(musescore_file)


def replace_extension(filename, new_extension):
    """Replace extension on filename with new_extension."""
    base = os.path.splitext(filename)[0]
    return f"{base}{new_extension}"


def extract_lyrics(musescore_file):
    export(musescore_file, ".metajson", True, False)
    meta_json_file = replace_extension(musescore_file, ".metajson")
    lyrics = (
        subprocess.check_output(["jq", "-r", ".lyrics", meta_json_file])
        .decode("utf-8")
        .strip()
    )
    os.remove(meta_json_file)
    return lyrics


def export_lyrics(musescore_file):
    """Write lyrics from musescore to file adjacent named .txt."""
    lyrics_filename = replace_extension(musescore_file, ".txt")
    lyrics = extract_lyrics(musescore_file)
    with open(lyrics_filename, "w", encoding="utf8") as lyrics_file:
        lyrics_file.write(lyrics)


def export_uncompressed(musescore_file):
    """Export from musescore to file adjacent with uncompressed musescore filename."""
    export(musescore_file, ".mscx", True, False)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Error: specify at most one file or directory at a time")
        sys.exit(1)
    arg = "."
    if len(sys.argv) == 2:
        arg = sys.argv[1]
    if os.path.isfile(arg):
        export_audio(arg)
        export_lyrics(arg)
    else:
        files = find_musescore_files(arg)
        for file in files:
            export_audio(file)
            export_lyrics(file)
