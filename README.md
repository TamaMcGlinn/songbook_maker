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

generate_index(songs, INDEX_PATH, "./liedboek_voorblad/")
```

To number songs explicitly, write your songs definition like:

```
songs = [
    {"name": "Hear_bliuw_mie_nei", "number": "2453"},
    {"name": "foar_de_pracht_fan_loft_en_wrald", "number": "2454"},
    {"name": "wes_stil_en_wit", "number": "2455"},
]

generate_index(songs, INDEX_PATH) # example without pdf preamble
```
