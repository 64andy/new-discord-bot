import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from fuzzywuzzy import fuzz, process
from music_tag import load_file
from music_tag.id3 import Id3File


def string_distance_ignoring_length(against: str, query: str) -> float:
    n1 = len(against)
    n2 = len(query)
    # Funky number that ensures the distance is 1.0 if one
    # string is a sub-string of another
    multiplier = (n1 + n2) / n2
    return process.extract(against, query.casefold()).ratio() * multiplier


@dataclass(frozen=True, order=True)
class SongData:
    album: str
    track_num: int
    artist: str
    title: str
    filename: str
    length: float

    @staticmethod
    def from_music_tag(song_data: Id3File) -> 'SongData':
        title = song_data.resolve('tracktitle').value
        # If a file has no title attribute, use its filename (minus the extension)
        if not title:
            title = Path(song_data.filename).stem

        return SongData(
            album=song_data.resolve('album').value,
            track_num=song_data.resolve('tracknumber').value,
            artist=song_data.resolve('artist').value,
            length=song_data.resolve('#length').value,
            title=title,
            filename=song_data.filename,
        )


def main():
    all_songs: List[SongData] = []
    root = "G:/Andrew/Music"
    for (dirname, _, filenames) in os.walk(root):
        for fname in filenames:
            song_data: Id3File = load_file(
                os.path.join(dirname, fname), err=None)
            if song_data is not None:
                all_songs.append(SongData.from_music_tag(song_data))
    albums: Dict[str, List[SongData]] = defaultdict(list)
    for song in all_songs:
        if song.album:
            albums[song.album].append(song)
    print("Total songs", len(all_songs))
    while True:
        column, query = input(">").split(maxsplit=1)
        if column == "song":
            best = process.extract(query, map(lambda s: s.title, all_songs), scorer=fuzz.partial_token_set_ratio)
            print(best)
            print("Playing:", best[0])
        elif column == "album":
            best = process.extract(query, albums.keys(), scorer=fuzz.partial_token_set_ratio)
            best_album = best[0][0]
            print(best)
            print(f"Playing: {best_album} with {len(albums[best_album])} songs")

        else:
            print("unknown column")
            


if __name__ == "__main__":
    main()
