# -*- coding: utf-8 -*-

import asyncio
import functools
import time
from typing import List

import discord
import yt_dlp
from discord.ext import commands

from .abstract_audio import AbstractAudio


# Silence useless bug reports messages
yt_dlp.utils.bug_reports_message = lambda: ''

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}


class YTDLError(commands.CommandInvokeError):
    pass


class YTDLSource(AbstractAudio):

    YTDL = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, data: dict):
        self.requester: discord.User = ctx.author
        self.channel: discord.TextChannel = ctx.channel
        self.data = data
        self.video_id = data["id"]
        self._ctx = ctx

    def __str__(self):
        return f'**{self.name}** by **{self.data["uploader"]}**'

    @classmethod
    async def from_ctx(cls, ctx: commands.Context, search: str) -> 'List[YTDLSource]':
        """
        Returns a list of the raw songs info in a search.
        If only one song is found it's a 1-len list
        If it's a playlist, every song in the playlist is added.
        """
        # Step 1. Ask YouTube for what the user searched for
        loop = asyncio.get_event_loop()
        partial = functools.partial(
            YTDLSource.YTDL.extract_info, search,
            download=False, process=True)

        start = time.perf_counter()
        data = await loop.run_in_executor(None, partial)
        end = time.perf_counter()
        print(f"from_ctx()'s YTDL query took {end-start:.3f}s")

        if data is None:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")

        # Step 2. Wrap the data on the video(s).
        data_to_process = None
        if 'entries' not in data:
            # Is a single video, so the whole data is about that video
            data_to_process = [data]
        elif '_type' in data and data['_type'] == 'playlist':
            # Is a playlist, each video is inside "entries"
            data_to_process = data['entries']
        else:
            print(
                f"!!! YTDLSource.from_ctx(): UNKNOWN RETURN TYPE with {search=}")

        if data_to_process is None or len(data_to_process) == 0:
            raise YTDLError(
                f"Couldn't find anything that matches `{search}`")
        return [YTDLSource(ctx, data) for data in data_to_process]

    async def generate_source(self) -> discord.FFmpegPCMAudio:
        loop = asyncio.get_event_loop()
        partial = functools.partial(
            YTDLSource.YTDL.extract_info, self.url,
            download=False, process=True, extra_info={'noplaylist': True})

        start = time.perf_counter()
        data = await loop.run_in_executor(None, partial)
        end = time.perf_counter()
        print(f"generate_source()'s YTDL query took {end-start:.3f}s")

        if data is None:
            raise YTDLError(f"Unable to find **{self.name}** ({self.url}).")

        return discord.FFmpegPCMAudio(source=data['url'], **FFMPEG_OPTIONS)

    def create_embed(self):
        return (
            discord.Embed(title='Now playing',
                          description=f'[{self.name}]({self.url})',
                          color=discord.Colour(0x1FA852))
            .add_field(name='Duration', value=self.parse_duration())
            .add_field(name='Requested by', value=self.requester.mention)
            .add_field(name='Uploader', value=f'[{self.data["uploader"]}]({self.data["uploader_url"]})')
            .set_image(url=self.data["thumbnail"])
        )

    @property
    def name(self) -> str:
        return self.data["title"]

    @property
    def url(self) -> str:
        return f"https://youtu.be/{self.video_id}"

    @property
    def length(self) -> int:
        return self.data["duration"]

    @property
    def context(self) -> commands.Context:
        return self._ctx
