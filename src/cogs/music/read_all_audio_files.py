import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import DefaultDict, Dict, List, Union

from thefuzz import fuzz, process
from music_tag import load_file
from music_tag.id3 import Id3File


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


def get_all_songs(filepath: str) -> List[SongData]:
    all_songs: List[SongData] = []
    for (dirname, _, filenames) in os.walk(filepath):
        for fname in filenames:
            full_path = os.path.join(dirname, fname)
            song_data: Id3File = load_file(full_path, err=None)
            if song_data is not None:
                all_songs.append(SongData.from_music_tag(song_data))
    return all_songs

# Annoyingly, `processor` is run against both the query AND the choices, so we need to do this type check


def album_processor(song: Union[str, SongData]) -> str:
    if isinstance(song, str):
        return song.lower()
    elif isinstance(song, SongData):
        # return song.album.lower()
        return f"{song.artist} {song.album}".lower()


def song_processor(song: Union[str, SongData]) -> str:
    if isinstance(song, str):
        return song.lower()
    elif isinstance(song, SongData):
        return f"{song.artist} {song.album} {song.title}".lower()


def main2():
    song1 = SongData("Currents", 1, "Tame Impala", "Let It Happen", ".", 180.0)
    song2 = SongData("Happy Ending", 1, "MIKA", "Life In Cartoon Motion", ".", 180.0)
    print(fuzz.partial_token_sort_ratio("let it happen", song_processor(song1)))
    print(fuzz.partial_token_sort_ratio("let it happen", song_processor(song2)))
    print(fuzz.partial_token_set_ratio("let it happen", song_processor(song1)))
    print(fuzz.partial_token_set_ratio("let it happen", song_processor(song2)))

def main():
    # all_songs = get_all_songs("G:/andrew/music")
    import pickle
    all_songs = pickle.load(open("all_songs.pkl", "rb"))
    albums: DefaultDict[str, list[SongData]] = defaultdict(list)
    for song in all_songs:
        if song.album:
            albums[song.album].append(song)
    fudged_albums = {album_processor(val[0]): key for (key, val) in albums.items()}
    print("Total songs", len(all_songs))
    while True:
        try:
            column, query = input(">").split(maxsplit=1)
        except ValueError:
            continue
        query_words = set(query.split())
        if column == "song":
            acceptable_songs = filter(lambda s: query_words.issubset(song_processor(s).split()), all_songs)
            best = process.extract(
                query, acceptable_songs, processor=song_processor, scorer=fuzz.token_sort_ratio, limit=5)
            print(best)
            print(f"Playing: {best[0][0].title} ({best[0][1]} conf)")
        elif column == "album":
            acceptable_songs = filter(lambda s: query_words.issubset(s.split()), fudged_albums)
            best = process.extractBests(
                query, acceptable_songs, scorer=fuzz.token_sort_ratio)
            best_album = best[0][0]
            best_album_name = fudged_albums[best_album]
            print(best)
            print(
                f"Playing: {best_album_name} with {len(albums[best_album_name])} songs")

        else:
            print("unknown column")


if __name__ == "__main__":
    main()
