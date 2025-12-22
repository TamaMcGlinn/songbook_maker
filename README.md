# Song Index

You can use song_index to package together a set of songs numbered either manually or
sequentially. Both pdf and html output is generated, such that you can listen to
the songs on the webpage. An optional preamble pdf can be included beforehand,
and a final index page will list first lines and titles alphabetically.

For example, this gives a songbook of 3 songs numbered 1 - 3:

```
#!/usr/bin/env python3

from song_index import generate_index, number_sequentially

INDEX_PATH = "./static/liedboek/index.html"


songs = number_sequentially(
    [
        "groot_is_Uw_trouw",
        "hij_die_rustig_en_stil",
        "ik_voel_de_winden_Gods_vandaag",
    ]
)

generate_index(songs, INDEX_PATH, language="dutch", frontpage_dir="./liedboek_voorblad/")
```

To number songs explicitly, or combine different languages, write your songs definition like:

```
songs = [
    {"language": "frisian", "name": "Hear_bliuw_mie_nei", "number": "5"},
    {"language": "danish", "name": "jeg_trænger_til_din_trøst", "number": "6a"},
    {"language": "dutch", "name": "groot_is_Uw_trouw", "number": "2455"},
]

generate_index(songs, INDEX_PATH)
```

frontpage_dir is an optional dir put before the song pdfs containing pdf's ed1.pdf ed2.pdf etc.
The one with the highest number is picked. If you also have ed2_rond.pdf, then the roundnote
variant also gets a preamble. You are recommended to keep a source file (e.g. LibreOffice) there
and whenever you plan to distribute / print your songbook, increment the version number / date
and re-export to edX.pdf and edX_rond.pdf 

## TODO

- Rename all occurences of rond to round. I just started out only supporting Dutch so some of the code may be commented / named in Dutch. The code should all be in English.
