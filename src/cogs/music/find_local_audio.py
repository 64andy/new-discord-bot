"""
A class for searching local files
"""
from collections import defaultdict
from itertools import islice
import logging
from math import inf
import os
import random
from dataclasses import dataclass
from pathlib import Path
import pprint
from typing import Callable, Dict, List, Optional, Tuple, Union

import discord
from music_tag import load_file
from music_tag.id3 import Id3File
from thefuzz import fuzz, process

MIN_SIMILARITY = 85  # Fuzzy search needs 85% confidence in the similarity
DISCORD_AUTOCOMPLETE_LIMIT = 25  # Discord autocomplete only allows 25 suggestions max


@dataclass(frozen=True)
class SongData:
    """Class for storing information about a local audio file"""

    album: str
    track_num: int
    artist: str
    title: str
    filepath: str
    length: float

    @staticmethod
    def from_music_tag(song_data: Id3File) -> "SongData":
        title = song_data.resolve("tracktitle").value
        # If a file has no title attribute, use its filename (minus the extension)
        if not title:
            title = Path(song_data.filename).stem

        return SongData(
            album=song_data.resolve("album").value or "<None>",
            track_num=song_data.resolve("tracknumber").value or "<None>",
            artist=song_data.resolve("artist").value or "<None>",
            length=song_data.resolve("#length").value,
            title=title,
            filepath=song_data.filename,
        )
    
    def __hash__(self) -> int:
        return hash(self.filepath)
    
    def __eq__(self, other: object) -> bool:
        """True if they both point to the same file"""
        return isinstance(other, self.__class__) and self.filepath == other.filepath
    
    def __lt__(self, other: 'SongData') -> bool:
        """
        Used for sorting songs by their track number 

        If a song has no track number, it'll be sorted to the end of the list
        If songs share a track number it'll sort by the title alphabetically
        """
        self_track_num = self.track_num if isinstance(self.track_num, int) else inf
        other_track_num = other.track_num if isinstance(other.track_num, int) else inf

        return (self_track_num, self.title.lower()) < (other_track_num, other.title.lower())




def _get_other_autocomplete_fields(interaction: discord.Interaction) -> Dict[str, str]:
    other_fields = {}
    for field in interaction.data["options"]:
        # For every populated autocomplete field that ISN'T this one...
        if not field.get("focused") and field["value"]: 
            other_fields[field["name"]] = field["value"]
    return other_fields


def _get_all_songs(filepath: str) -> List[SongData]:
    all_songs = []
    for (dirname, _, filenames) in os.walk(filepath):
        for fname in filenames:
            full_path = os.path.join(dirname, fname)
            song_data: Id3File = load_file(full_path, err=None)
            if song_data is not None:
                all_songs.append(SongData.from_music_tag(song_data))

    return all_songs


def _tag_processor(
    attr_name,
) -> Callable[[Union[str, SongData]], str]:
    def inner(song_data) -> str:
        # Might be a tuple of type (song, confidence)
        while isinstance(song_data, tuple):
            song_data = song_data[0]
        # Check 1: It's a raw SongData from all_songs or something.
        # So, get the string property we want
        if isinstance(song_data, SongData):
            return getattr(song_data, attr_name).lower()
        # This check exists before the processor is run against the query as well
        elif isinstance(song_data, str):
            return song_data.lower()

    return inner


class LocalAudioLibrary:
    all_songs: List[SongData]

    def __init__(self, audio_directory: str):
        self.all_songs = _get_all_songs(audio_directory)
        self.field_to_song = {
            "title": defaultdict(list),
            "artist": defaultdict(list),
            "album": defaultdict(list),
            }
        for song in self.all_songs:
            self.field_to_song["title"][song.title].append(song)
            self.field_to_song["artist"][song.artist].append(song)
            self.field_to_song["album"][song.album].append(song)

    def find_possible_songs(self, **kwargs) -> List[SongData]:
        best = self.all_songs

        def _merge(sd: Union[SongData, Tuple[SongData, int]]):
            total_conf = 0
            # 
            while isinstance(sd, tuple):
                total_conf += sd[1]
                sd = sd[0]
            return (sd, total_conf)

        for (attr_name, query) in kwargs.items():
            if attr_name and query:
                # Don't accept anything longer than the query string (searching "Mezzanine" shouldn't match "Me")
                best = [
                    song
                    for song in best
                    if len(_tag_processor(attr_name)(song)) >= len(query)
                ]
                best = process.extractBests(
                    query,
                    best,
                    processor=_tag_processor(attr_name),
                    scorer=fuzz.ratio,  # Scorer to be improved
                    score_cutoff=MIN_SIMILARITY,
                    limit=None,
                )
                print(f"{attr_name!r} search. {len(best)} result(s):")
                best = [_merge(entry) for entry in best]
                pprint.pprint(best[:10])
                print("===")

        return [song for (song, _conf) in best]

    def get_autocomplete_suggestions(self, attr_name):
        async def inner(
            interaction: discord.Interaction, query: Optional[str]
        ) -> List[discord.app_commands.Choice]:
            other_autocomplete_fields = _get_other_autocomplete_fields(interaction)

            # * IF: No fields have been entered
            if not query.strip() and not other_autocomplete_fields:
                # If the user hasn't typed anything, return random choices
                
                all_options = list(self.field_to_song[attr_name])
                return [
                    discord.app_commands.Choice(name=option[:100], value=option[:100])
                    for option in random.choices(all_options, k=DISCORD_AUTOCOMPLETE_LIMIT)
                ]
            # Only show songs that match the other fields
            possible_songs = set()  ??????????
            for (name, value) in other_autocomplete_fields.items():
                possible_songs = filter(
                    lambda s: getattr(s, name) == value, possible_songs
                )
            possible_songs = sorted(possible_songs)
            # Remove duplicates, keeping order
            all_suggestions = list(dict.fromkeys(
                getattr(s, attr_name)
                for s in possible_songs
                if len(query) <= len(getattr(s, attr_name))
            ))

            # * IF: No value for this field has been entered, show what CAN be entered
            if not query.strip():
                best = [(song, None) for song in all_suggestions]
            else:
                best = process.extractBests(
                    query,
                    all_suggestions,
                    scorer=fuzz.partial_ratio,  # Scorer to be improved
                    score_cutoff=MIN_SIMILARITY,
                    limit=25,
                )

            print(f"Total of {len(best)} {attr_name!r} autocomplete suggestions with {query!r}.\n{pprint.pformat(best[:6])}")
            # Remove the confidence value, and only take 25 values at most
            best = (song for (song, _conf) in islice(best, DISCORD_AUTOCOMPLETE_LIMIT))
            return [
                discord.app_commands.Choice(name=name[:100], value=name[:100])
                for name in best
            ]

        return inner


if __name__ == "__main__":
    lib = LocalAudioLibrary("G:/Andrew/Music")
    lib.find_possible_songs(artist="Can", title="Bring Me Coffee Or Tea")
