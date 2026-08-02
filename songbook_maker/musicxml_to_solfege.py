#!/usr/bin/env python3
"""
musicxml_to_solfege.py

Read a single-part MusicXML file and output:
    [(duration_in_quarter_notes, "do"), ...]

Requires:
    pip install music21
"""

from __future__ import annotations

import argparse
from typing import Iterable

from music21 import chord, converter, key, note, stream

SOLFEGE_MAJOR = ["do", "re", "mi", "fa", "so", "la", "ti"]

# Chromatic movable-do syllables by scale degree alteration.
# Example in C major:
#   C# = raised do = di
#   Db = lowered re = ra
RAISED = {
    "do": "di",
    "re": "ri",
    "mi": "mi",  # E# is enharmonically F; uncommon spelling
    "fa": "fi",
    "so": "si",
    "la": "li",
    "ti": "ti",  # B# is enharmonically C; uncommon spelling
}

LOWERED = {
    "do": "do",  # Cb is enharmonically B; uncommon spelling
    "re": "ra",
    "mi": "me",
    "fa": "fe",
    "so": "se",
    "la": "le",
    "ti": "te",
}

STEP_INDEX = {
    "C": 0,
    "D": 1,
    "E": 2,
    "F": 3,
    "G": 4,
    "A": 5,
    "B": 6,
}


def get_single_part(score: stream.Score) -> stream.Part:
    parts = score.parts
    if len(parts) != 1:
        raise ValueError(f"Expected exactly one part, found {len(parts)}.")
    return parts[0]


def get_key(part: stream.Part, override_key: str | None = None) -> key.Key:
    """
    Determine the key.

    If --key is supplied, use it directly, e.g. C, G, F#, Bb.
    Otherwise use the first Key or KeySignature found in the part.
    If only a KeySignature is present, interpret it as a major key.
    """
    if override_key:
        return key.Key(override_key)

    found_key = part.recurse().getElementsByClass(key.Key).first()
    if found_key is not None:
        return found_key

    found_sig = part.recurse().getElementsByClass(key.KeySignature).first()
    if found_sig is not None:
        return found_sig.asKey("major")

    return key.Key("C")


def key_signature_alter_for_step(k: key.Key, step: str) -> int:
    """
    Return the accidental normally present for a letter name in the key.

    Example:
        In D major:
            F -> +1
            C -> +1
            D -> 0
    """
    ks = key.KeySignature(k.sharps)
    altered = ks.alteredPitches

    for p in altered:
        if p.step == step:
            return int(p.accidental.alter)

    return 0


def pitch_to_solfege(p, k: key.Key) -> str:
    """
    Convert a music21 Pitch to movable-do solfege in a major key.

    The diatonic scale degree is based on the letter name relative to the tonic.
    The chromatic syllable is based on the note's accidental compared with
    the accidental expected in the key signature.

    In C major:
        C  -> do
        C# -> di
        Db -> ra
        D  -> re
        Eb -> me
        F# -> fi
        Bb -> te
    """
    tonic_step = k.tonic.step
    degree_index = (STEP_INDEX[p.step] - STEP_INDEX[tonic_step]) % 7
    base_syllable = SOLFEGE_MAJOR[degree_index]

    actual_alter = int(p.accidental.alter) if p.accidental else 0
    expected_alter = key_signature_alter_for_step(k, p.step)
    relative_alter = actual_alter - expected_alter

    if relative_alter == 0:
        return base_syllable
    if relative_alter == 1:
        return RAISED[base_syllable]
    if relative_alter == -1:
        return LOWERED[base_syllable]

    # Rare cases: double sharps/flats
    if relative_alter > 1:
        return RAISED[base_syllable] + "+" * (relative_alter - 1)
    return LOWERED[base_syllable] + "-" * (abs(relative_alter) - 1)


def iter_pitched_events(part: stream.Part) -> Iterable[tuple[float, object]]:
    """
    Yield (quarterLength, pitch) events.

    Rests are skipped.
    Chords are rejected because the requested output has one note string
    per duration.
    Tied notes are merged into one duration where possible.
    """
    pending_pitch = None
    pending_duration = 0.0
    pending_solfege_pitch = None

    for el in part.flatten().notesAndRests:
        if isinstance(el, note.Rest):
            continue

        if isinstance(el, chord.Chord):
            raise ValueError(
                "Found a chord. This script expects a monophonic single part."
            )

        if not isinstance(el, note.Note):
            continue

        dur = float(el.duration.quarterLength)
        tie_type = el.tie.type if el.tie else None

        if tie_type in ("start", "continue"):
            if pending_pitch is None:
                pending_pitch = el.pitch.nameWithOctave
                pending_solfege_pitch = el.pitch
                pending_duration = dur
            else:
                pending_duration += dur
            continue

        if tie_type == "stop":
            if pending_pitch == el.pitch.nameWithOctave:
                pending_duration += dur
                yield pending_duration, pending_solfege_pitch
                pending_pitch = None
                pending_solfege_pitch = None
                pending_duration = 0.0
            else:
                # Defensive fallback for malformed ties.
                yield dur, el.pitch
            continue

        # Untied note
        if pending_pitch is not None:
            # Flush malformed dangling tie.
            yield pending_duration, pending_solfege_pitch
            pending_pitch = None
            pending_solfege_pitch = None
            pending_duration = 0.0

        yield dur, el.pitch

    if pending_pitch is not None:
        yield pending_duration, pending_solfege_pitch


def musicxml_to_solfege(
    path: str, override_key: str | None = None
) -> list[tuple[float, str]]:
    score = converter.parse(path)
    part = get_single_part(score)
    k = get_key(part, override_key)

    result = []
    for duration, pitch_obj in iter_pitched_events(part):
        result.append((duration, pitch_to_solfege(pitch_obj, k)))

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a single-part MusicXML file to solfege tuples."
    )
    parser.add_argument("xml_file", help="Path to MusicXML .xml file")
    parser.add_argument(
        "--key",
        help='Override key, e.g. "C", "G", "F#", "Bb". Defaults to the file key signature.',
    )
    args = parser.parse_args()

    tuples = musicxml_to_solfege(args.xml_file, args.key)
    print(tuples)


if __name__ == "__main__":
    main()
