"""
A class for searching local files
"""
from itertools import islice
import logging
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


@dataclass(frozen=True, order=True)
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


def _get_other_autocomplete_fields(interaction: discord.Interaction) -> Dict[str, str]:
    other_fields = {}
    for field in interaction.data["options"]:
        if (
            not field.get("focused") and field["value"]
        ):  # If this isn't the current field, and something's been typed into the field
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

    # Sort by track number (ignoring non-integer values)
    all_songs.sort(key=lambda song: isinstance(song.track_num, int) and song.track_num)
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
        self.title_list = list({s.title for s in self.all_songs})
        self.artist_list = list({s.artist for s in self.all_songs})
        self.album_list = list({s.album for s in self.all_songs})

    def find_possible_songs(self, **kwargs) -> List[SongData]:
        best = self.all_songs

        def _merge(sd: Union[SongData, Tuple[SongData, int]]):
            total_conf = 0
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

            # * IF: No other fields have been entered
            if not query.strip() and not other_autocomplete_fields:
                # If the user hasn't typed anything, return random choices
                defaults = [
                    discord.app_commands.Choice(name=option[:100], value=option[:100])
                    for option in random.choices(
                        getattr(self, attr_name + "_list"), k=DISCORD_AUTOCOMPLETE_LIMIT
                    )
                ]
                return defaults
            # Cut down the possibilities, depending on the other entered fields
            possible_songs = self.all_songs
            for (name, value) in other_autocomplete_fields.items():
                possible_songs = filter(
                    lambda s: getattr(s, name) == value, possible_songs
                )
            possible_songs = sorted(possible_songs, key=lambda s: isinstance(s, str) and s.track_num)
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
