# -*- coding: utf-8 -*-

from typing import List
from sys import stderr

from discord import FFmpegPCMAudio, Embed, Colour
from discord.ext import commands

from .abstract_audio import AbstractAudio

FFMPEG_OPTIONS = {
    'options': '-vn',
    'stderr': stderr,
    # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}


"""
An audio source for local music files.
"""
class LocalAudioSource(AbstractAudio):

    def __init__(self, ctx: commands.Context, filepath: str):
        self._ctx = ctx
        self.filepath = filepath

    @classmethod
    async def from_ctx(cls, ctx: commands.Context, filepath: str) -> 'List[LocalAudioSource]':
        return [LocalAudioSource(ctx, filepath)]

    async def generate_source(self) -> FFmpegPCMAudio:
        return FFmpegPCMAudio(self.filepath, **FFMPEG_OPTIONS)

    def create_embed(self) -> Embed:
        return Embed(title='Now playing',
                     description=self.name,
                     color=Colour.blue()
                     )

    def __str__(self):
        return self.name

    @property
    def name(self) -> str:
        return self.filepath

    @property
    def url(self) -> None:
        return None

    @property
    def length(self) -> None:
        return None

    @property
    def context(self) -> commands.Context:
        return self._ctx
