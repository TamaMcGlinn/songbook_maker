#!/usr/bin/env python3

import unittest

from song_index import *


class TestSongIndex(unittest.TestCase):
    def test_get_index_of_titles_and_first_lines(self):
        songlist = number_sequentially(["k_zie_het_land", "groot_is_Uw_trouw"])
        apply_language(songlist, "dutch")
        index = get_index_of_titles_and_first_lines(songlist)
        self.assertEqual(index, [IndexEntry(entry='Groot is Uw trouw, o Heer', number='2', type=IndexEntryType.TITLE), IndexEntry(entry="'k Zie het land", number='1', type=IndexEntryType.TITLE)])

if __name__ == "__main__":
    unittest.main()
