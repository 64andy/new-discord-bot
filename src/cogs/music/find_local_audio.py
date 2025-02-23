"""
A class for searching local files
"""
from collections import defaultdict
import logging
from math import inf
import os
import random
from dataclasses import dataclass
from pathlib import Path
import pprint
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

import discord
from music_tag import load_file
from music_tag.id3 import Id3File
from thefuzz import fuzz, process

AUTOCOMPLETE_MIN_SIMILARITY = 85    # When giving auto-complete options, we'll match 85% similarity
SELECTION_MIN_SIMILARITY = 95       # When actually picking the songs, it'll match anything 95% similar
DISCORD_AUTOCOMPLETE_LIMIT = 25     # Discord autocomplete only allows 25 suggestions max


logger = logging.getLogger(__name__)

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
            try:
                song_data: Id3File = load_file(full_path, err=None)
                if song_data is not None:
                    all_songs.append(SongData.from_music_tag(song_data))
            except NotImplementedError as e:
                logger.warning(f"Unsupported file: {full_path!r} ({e!r})")
            except Exception as e:
                logger.error(f"Error parsing file {full_path!r}: {type(e).__name__}: {e!r}")
                

    return all_songs

def get_x_unique_values(items: Iterable, x: int) -> Iterable:
    """Returns upto `x` non-duplicate items from `items`"""
    seen = set()
    for val in items:
        if len(seen) >= x:
            break
        if val in seen:
            continue
        seen.add(val)
        yield val



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
        self.field_to_song: Dict[str, Dict[str, Set[SongData]]] = {
            "title": defaultdict(set),
            "artist": defaultdict(set),
            "album": defaultdict(set),
        }
        for song in self.all_songs:
            self.field_to_song["title"][song.title].add(song)
            self.field_to_song["artist"][song.artist].add(song)
            self.field_to_song["album"][song.album].add(song)

    # TODO: Replace the song selection code to NOT use fuzzy search
    #       We have autocomplete, the user should be using that.

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
                    score_cutoff=SELECTION_MIN_SIMILARITY,
                    limit=None,
                )
                print(f"{attr_name!r} search. {len(best)} result(s):")
                best = [_merge(entry) for entry in best]
                pprint.pprint(best[:10])
                print("===")

        return [song for (song, _conf) in best]

    def _autocomplete_give_random_values(self, attr_name) -> List[str]:
        all_options = list(self.field_to_song[attr_name].keys())
        random.shuffle(all_options)
        return all_options
    
    def _autocomplete_give_closest_match(self, query: str, attr_name: str, other_autocomplete_fields: Dict[str, str]) -> Iterable[SongData]:
        """Uses fuzzy search to find the closest match"""
        possible_songs = self._autocomplete_filtered_from_other_fields(other_autocomplete_fields)
        get_tag = _tag_processor(attr_name)
        # If the `query` is longer than the searched field, don't consider it.
        # This is so searching for, e.g., "Mezzanine" doesn't cause "Me" to show up
        possible_songs = filter(lambda s: len(query) <= len(get_tag(s)), possible_songs)
        possible_songs = process.extractBests(
            query=query,
            choices=possible_songs,
            processor=get_tag,
            scorer=fuzz.partial_ratio,  # Scorer to be improved
            score_cutoff=AUTOCOMPLETE_MIN_SIMILARITY,
            limit=None
        )

        # Sort by highest confidence, then by string length similarity
        # e.g. Searching for "ain't" will put "Ain't" at the top,
        #      and "Two Out Of Three Ain't Bad" lower
        possible_songs.sort(key=lambda kv: (kv[1], len(get_tag(kv[0])) - len(query)))
        # Return without the confidence value
        return (song for (song, _conf) in possible_songs)

    def _autocomplete_filtered_from_other_fields(self, other_autocomplete_fields: Dict[str, str]) -> Set[SongData]:
        # If no other autocomplete fields exist, just search everything
        if len(other_autocomplete_fields) == 0:
            return self.all_songs
        # Using an iterator, so our first value can "populate" the set
        it = iter(other_autocomplete_fields.items())
        (name, value) = next(it)
        possible_songs = self.field_to_song[name][value]
        # ... then use the remaining fields to filter
        for (name, value) in it:
            possible_songs.intersection_update(self.field_to_song[name][value])
        return possible_songs

    def get_autocomplete_suggestions(self, attr_name):
        async def inner(
            interaction: discord.Interaction, query: Optional[str]
        ) -> Iterable[discord.app_commands.Choice]:
            other_autocomplete_fields = _get_other_autocomplete_fields(interaction)
            # * IF: not a single field's been entered, just return random values
            if not query.strip() and not other_autocomplete_fields:
                possible_songs = self._autocomplete_give_random_values(attr_name)
                return (discord.app_commands.Choice(name=name, value=name)
                        for name in possible_songs[:DISCORD_AUTOCOMPLETE_LIMIT])
            # * IF: someone's typed into the field, return the most likely values
            elif query.strip():
                possible_songs = self._autocomplete_give_closest_match(query, attr_name, other_autocomplete_fields)
            else:
                possible_songs = self._autocomplete_filtered_from_other_fields(other_autocomplete_fields)
                # * If album's been set, return in track-number order
                # * (So the `title` field shows 1st, 2nd, 3rd... songs in order)
                if attr_name == "title" and other_autocomplete_fields.get('album'):
                    possible_songs = sorted(possible_songs)
                # * Otherwise, sort by the current field
                else:
                    possible_songs = sorted(possible_songs, key=lambda s: getattr(s, attr_name))
            # We only wanna see data from the current field
            possible_songs = map(lambda s: getattr(s, attr_name), possible_songs)
            # Return 25 (the API limit) non-duplicating values
            # (Non-duplicating, because every song in an album adds the same album name)
            return (
                discord.app_commands.Choice(name=name, value=name)
                for name in get_x_unique_values(possible_songs, DISCORD_AUTOCOMPLETE_LIMIT)
            )

        return inner


if __name__ == "__main__":
    # Debugging script, consider removing
    import pickle
    local_library = LocalAudioLibrary("src")
    with open("all_songs.pkl", "rb") as file:
        all_songs: List[SongData] = pickle.load(file)
    new_songs = [SongData(
            album=song.album,
            track_num=song.track_num,
            artist=song.artist,
            title=song.title,
            filepath=song.filename,
            length=song.length
        )
        for song in all_songs
    ]
    
    local_library.all_songs = new_songs
    x = local_library._autocomplete_give_closest_match(query="Mouth", attr_name="album", other_autocomplete_fields={})
    print(x)
