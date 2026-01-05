# -*- coding: utf-8 -*-

import asyncio
from typing import List

import discord
import yt_dlp
from discord.ext import commands

from .abstract_audio import AbstractAudio


YTDL_OPTIONS = {
    "format": "wa", # Worst audio, because sometimes Bandcamp is too good
    "extractaudio": True,
    "audioformat": "mp3",
    "restrictfilenames": True,
    "noplaylist": False,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}
YTDL = yt_dlp.YoutubeDL(YTDL_OPTIONS)

# YT-DLP uses a format selector to choose which version to download.
# In our case, we want the one with best audio.
FORMAT_SELECTOR = YTDL.build_format_selector(YTDL_OPTIONS['format'])

FFMPEG_OPTIONS = {
    "options": "-vn",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
}

class YTDLError(commands.CommandError):
    pass


def _find_video_url(data: dict) -> str:
    """
    Searches the video information returned by yt-dlp, trying to find
    the backing URL from which the bot can play.
    """
    # Websites like YouTube can provide hundreds of different ways of seeing a video
    #  (The video at 144p, 720p, 1080p, audio only, auto-dubbed audio...)
    # However, we need the SINGLE URL to play.
    # ---
    # YT-DLP figures out which one of these is the one you want, using
    #  the format string in a "format_selector"
    # https://github.com/yt-dlp/yt-dlp/blob/cec1f1df792fe521fff2d5ca54b5c70094b3d96a/yt_dlp/YoutubeDL.py#L3047
    format_to_download = YTDL._select_formats(data['formats'], FORMAT_SELECTOR)
    if len(format_to_download) == 0:
        raise YTDLError(f"Unable to find an audio version of {data['url']}")
    best_format = format_to_download[-1]
    return best_format['url']


class YTDLSource(AbstractAudio):

    YTDL = YTDL

    def __init__(self, data: dict, added_by: discord.User):
        self.data = data
        self.video_id = data["id"]
        self.requester = added_by

    def __str__(self):
        return f'**{self.name}** by **{self.artist}**'

    @classmethod
    async def from_query(
        cls, search: str, added_by: discord.User
    ) -> "List[YTDLSource]":
        """
        Returns a list of the raw songs info in a search.
        If only one song is found it's a 1-len list
        If it's a playlist, every song in the playlist is added.
        """
        ### Note: All from_query() does is grab information about the provided query.
        ### If it's a URL, this checks it exists. If it's a search, this grabs the first result.
        ### If it's a URL for a playlist, this grabs each song.
        loop = asyncio.get_event_loop()
        # Step 1. Ask YouTube for what the user searched for
        # WARNING: `process=True` is VERY expensive, but gives us info like the uploader easier
        get_song_info = lambda: YTDL.extract_info(search, download=False, process=True)
        data = await loop.run_in_executor(None, get_song_info)
        # yt-dlp's API changed: Now, if you do a text search (alexa play idkhow), it uses the 'generic' extractor which is useless
        # We need to change our query to `ytsearch:idkhow` so it'll use the appropriate extractors
        if data.get('extractor') == 'generic':
            get_song_info = lambda: YTDL.extract_info(f"ytsearch:{search}", download=False, process=False)
            data = await loop.run_in_executor(None, get_song_info)


        if data is None:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")

        # Step 2. Wrap the data on the video(s).
        data_to_process = None
        if "entries" not in data:
            # Is a single video, so the whole data is about that video
            data_to_process = [data]
        elif "_type" in data and data["_type"] == "playlist":
            # Is a playlist, each video is inside "entries"
            data_to_process = list(data["entries"]) # When process=False, 'entries' is a generator
        else:
            print(f"!!! YTDLSource.from_query(): UNKNOWN RETURN TYPE with {search=}")

        if data_to_process is None or len(data_to_process) == 0:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")
        return [
            YTDLSource(data, added_by)
            for data in data_to_process
        ]

    async def generate_source(self) -> discord.FFmpegPCMAudio:
        loop = asyncio.get_event_loop()
        partial = lambda: YTDL.extract_info(
            self.url,
            download=False,
            process=False,
            extra_info={"noplaylist": True},
        )

        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError(f"Unable to find **{self.name}** ({self.url}).")
        
        song_url = _find_video_url(data)

        return discord.FFmpegPCMAudio(source=song_url, **FFMPEG_OPTIONS)

    def create_embed(self):
        embed = (
            discord.Embed(
                title="Now playing",
                description=f"[{self.name}]({self.url})",
                color=discord.Colour(0x1FA852),
            )
            .add_field(name="Duration", value=self.parse_duration())
            .add_field(name="Requested by", value=self.requester.mention)
            .set_image(url= f"https://i.ytimg.com/vi/{self.video_id}/hqdefault.jpg")
        )
        
        # Some autogenerated music vids don't specify this data
        if "uploader" not in self.data:         # No uploader or URL
            uploader = "<Not Specified>"
        elif "uploader_urL" not in self.data:   # Just no URL (Can happen)
            uploader = self.data['uploader']
        else:                                   # Link to the channel
            uploader = f'[{self.data["uploader"]}]({self.data["url"]})'

        return embed.add_field(name="Uploader", value=uploader)

    @property
    def name(self) -> str:
        return self.data["title"]

    @property
    def url(self) -> str:
        return self.data.get('webpage_url') or self.data.get('original_url')

    @property
    def length(self) -> int:
        return self.data["duration"]
    
    @property
    def artist(self) -> str:
        return (self.data.get('uploader')   # YouTube
                or self.data.get('artist')  # Most other services
                or "<UNKNOWN ARTIST>")      # If you see this, try fixing it
