# -*- coding: utf-8 -*-

from sys import stderr

from discord import FFmpegPCMAudio, Embed, Colour, User

from src.cogs.music.find_local_audio import SongData

from .abstract_audio import AbstractAudio

FFMPEG_OPTIONS = {
    "options": "-vn",
    "stderr": stderr,
    # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}


class LocalAudioSource(AbstractAudio):
    """
    An audio source for local music files.
    """

    def __init__(self, song_data: SongData, added_by: User):
        self.song_data = song_data
        self.requester = added_by

    async def generate_source(self) -> FFmpegPCMAudio:
        return FFmpegPCMAudio(self.song_data.filepath, **FFMPEG_OPTIONS)

    def create_embed(self) -> Embed:
        track_num = self.song_data.track_num
        if track_num is None:
            track_num = "N/A"
        return (
            Embed(title="Now playing", description=self.name, color=Colour.blue())
            .add_field(name="#",            value=track_num)
            .add_field(name="Artist",       value=self.song_data.artist)
            .add_field(name="Album",        value=self.song_data.album)
            .add_field(name="Duration",     value=self.parse_duration())
            .add_field(name="Requested by", value=self.requester.mention)
        )

    def __str__(self):
        return f"**{self.name}** by **{self.song_data.artist}**"

    @property
    def name(self) -> str:
        return self.song_data.title

    @property
    def url(self) -> None:
        return None

    @property
    def length(self) -> None:
        return self.song_data.length
