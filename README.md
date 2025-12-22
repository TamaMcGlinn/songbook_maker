# Song Index

You can use song_index to package together a set of songs numbered either manually or
sequentially. Both pdf and html output is generated, such that you can listen to
the songs on the webpage. An optional preamble pdf can be included beforehand,
and a final index page will list first lines and titles alphabetically.

As an example, see [anabaptist.nl/songbooks](https://www.anabaptist.nl/songbooks).

## Installation

```
python3 -m pip install "songbook_maker"
```

## Usage

You need to write a small python script naming the songs you will use,
and place each song as an uncompressed MuseScore file in a directory
with the same name as the filename. For example, if you have these files:

```
$ tree -L 10
.
├── build_example.py
└── static
    └── songs
        ├── danish
        │   └── din_rigsag_Jesus_være_skal
        │       └── din_rigsag_Jesus_være_skal.mscx
        ├── dutch
        │   ├── groot_is_Uw_trouw
        │   │   └── groot_is_Uw_trouw.mscx
        │   ├── hij_die_rustig_en_stil
        │   │   └── hij_die_rustig_en_stil.mscx
        │   └── ik_voel_de_winden_Gods_vandaag
        │       └── ik_voel_de_winden_Gods_vandaag.mscx
        └── frisian
            └── Hear_bliuw_mie_nei
                └── Hear_bliuw_mie_nei.mscx

10 directories, 6 files
```

### build_example.py

This gives a songbook of 3 Dutch songs numbered 1 - 3:

```
#!/usr/bin/env python3

from songbook_maker.song_index import generate_index, number_sequentially

INDEX_PATH = "./static/my_example_songbook/index.html"


songs = number_sequentially(
    [
        "groot_is_Uw_trouw",
        "hij_die_rustig_en_stil",
        "ik_voel_de_winden_Gods_vandaag",
    ]
)

generate_index(
    songs, INDEX_PATH, language="dutch", frontpage_dir="./liedboek_voorblad/"
)
```

To number songs explicitly, or combine different languages, write:

```
songs = [
    {"language": "frisian", "name": "Hear_bliuw_mie_nei", "number": "5"},
    {"language": "danish", "name": "jeg_trænger_til_din_trøst", "number": "6a"},
    {"language": "dutch", "name": "groot_is_Uw_trouw", "number": "2455"},
]

generate_index(songs, INDEX_PATH)
```

Assuming you ran both variants, this will result in these master output files:

```
├── static
│   ├── my_example_songbook
│   │   ├── all.pdf
│   │   ├── all_rond.pdf
│   │   └── index.html
```

And also for each song:
- unnumbered PDF
- numbered pdf for each number used
- for each of above PDF also a "_rond.pdf" with round notes instead of Aikin shapenotes
- 4 mp3's for the voices (omitted if melody is shared, explained further down)
- .txt with just the song text (all on one line)

For example, static/songs/dutch/groot_is_Uw_trouw would have:

```
├── 1_groot_is_Uw_trouw.pdf
├── 1_groot_is_Uw_trouw_rond.pdf
├── 2455_groot_is_Uw_trouw.pdf
├── 2455_groot_is_Uw_trouw_rond.pdf
├── groot_is_Uw_trouw-Alto.mp3
├── groot_is_Uw_trouw-Bass.mp3
├── groot_is_Uw_trouw.mscx
├── groot_is_Uw_trouw.pdf
├── groot_is_Uw_trouw_rond.pdf
├── groot_is_Uw_trouw-Soprano.mp3
├── groot_is_Uw_trouw-Tenor.mp3
└── groot_is_Uw_trouw.txt
```

## Optional preamble (frontpage)

frontpage_dir is an optional dir put before the song pdfs in final output.
You need to put pdf's in there called edX.pdf (e.g. ed1.pdf ed2.pdf)
The one with the highest number is picked. If you also have ed2_rond.pdf, then the roundnote
variant also gets a preamble. You are recommended to keep a source file (e.g. LibreOffice) there
and whenever you plan to distribute / print your songbook, increment the version number / date
and re-export to edX.pdf and edX_rond.pdf.

## Sharing melodies

As an optimization, songs can be marked as sharing audio files; since these are quite large and
will often be shared across different language renditions of the same song. To do so, add a file
in songs/ called shared_melodies.txt as follows:

### shared_melodies.txt

```
# optional comments start with a hash
# first element has audio exported, others share the audio files
# each line should be: language/title [language/title]*
# for example:
english/rock_of_ages dutch/rots_der_eeuwen
frisian/wes_stil_en_wit dutch/wees_stil_en_weet english/be_still_and_know
dutch/Abba_Vader frisian/Abba_Heit
dutch/hoe_groot_zijt_Gij english/how_great_Thou_art
```

## TODO

- Rename all occurences of rond to round. I just started out only supporting Dutch so some of the code may be commented / named in Dutch. The code should all be in English.
- It shouldn't be necessary to keep the old preamble pdf's. If a user wants to go back and
print an old version, they will need to reset their own versions of all the songs and the list
of included songs anyway (e.g. using git) so there's not really any point - this should be simplified.
- It's probably a common error to include compressed MuseScore files, we could automatically convert them if so. The reason I haven't is that the user needs to know - otherwise they will go to recent files > compressed musescore file and then songbook_maker would need to re-export to uncompressed I guess. Just easier to error out, but maybe we can prompt the user if it's okay to convert and then delete the compressed version?
- Not everyone probably wants their song's source files to be in the static/ dir, as that makes them public as well. Add a parameter for the top-level song dir to read from and to write to so they can each be different from "static/"
