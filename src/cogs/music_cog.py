# -*- coding: utf-8 -*-

"""
https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d

Copyright (c) 2019 Valentin B.

A simple music bot written in discord.py using youtube-dl.

Though it's a simple example, music bots are complex and require much time and knowledge until they work perfectly.
Use this as an example or a base for your own bot and extend it as you want. If there are any bugs, please let me know.

Requirements:

Python 3.5+
pip install -U discord.py pynacl yt-dlp

You also need FFmpeg in your PATH environment variable or the FFmpeg.exe binary in your bot's directory on Windows.
"""

import asyncio
import functools
import itertools
import math
import random
from typing import List

import discord
import yt_dlp
from async_timeout import timeout
from discord.ext import commands

# Silence useless bug reports messages
yt_dlp.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
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
        # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        if source is not None:
            super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int( data.get('duration', 0) ))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return f'**{self.title}** by **{self.uploader}**'

    @classmethod
    async def get_info(cls, ctx, search: str, *, loop: asyncio.BaseEventLoop = None) -> 'List[YTDLSource]':
        """
        Returns a list of the raw songs info in a search.
        If only one song is found it's a 1-len list
        If it's a playlist, take a guess.

        Note: DO NOT RELY ON THIS FOR YOUR STREAM SOURCE
        These are husks, these 'YTDLSource's have no player
        This is because YT download links expire REAL quick
        When you wanna play, use the proper `create_source`
        """
        loop = loop or asyncio.get_event_loop()
        print('is this just real fucking slow?')
        partial = functools.partial(
            cls.ytdl.extract_info, search, download=False, process=True)
        data = await loop.run_in_executor(None, partial)
        print('it seems so')
        if data is None:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")

        process_info = []

        if 'entries' not in data:
            # Is a single video
            process_info.append(data)
        elif '_type' in data and data['_type'] == 'playlist':
            # Is a playlist
            for entry in data['entries']:
                if entry:
                    process_info.append(entry)
                else:
                    print(f"Ok it can be false? idk, look for me.\n{entry}")

        if not process_info:
            raise YTDLError(
                f"Couldn't find anything that matches `{search}`")
        process_info = [YTDLSource(ctx, source=None, data=info) for info in process_info]
        return process_info

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None) -> 'List[YTDLSource]':
        loop = loop or asyncio.get_event_loop()
        partial = functools.partial(
            cls.ytdl.extract_info, search, download=False, process=True,
            extra_info={'noplaylist': True})
        data = await loop.run_in_executor(None, partial)
        if data is None:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")

        source = cls(ctx, discord.FFmpegPCMAudio(data['url'], **cls.FFMPEG_OPTIONS), data=data)
        return source

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append(f'{days} days')
        if hours > 0:
            duration.append(f'{hours} hours')
        if minutes > 0:
            duration.append(f'{minutes} minutes')
        if seconds > 0:
            duration.append(f'{seconds} seconds')

        return ', '.join(duration)


class Song:
    __slots__ = ('data', 'requester')

    def __init__(self, data: YTDLSource, requester: discord.User):
        self.data = data
        self.requester = requester

    def create_embed(self):
        embed = (
            discord.Embed(title='Now playing',
                          description=f'[{self.data.title}]({self.data.url})',
                          color=discord.Colour(0x38B92A))
            .add_field(name='Duration', value=self.data.duration)
            .add_field(name='Requested by', value=self.requester.mention)
            .add_field(name='Uploader', value=f'[{self.data.uploader}]({self.data.uploader_url})')
            .set_image(url=self.data.thumbnail)
        )

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current: Song = None
        self.voice: discord.VoiceClient = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    if self.voice:
                        await self._ctx.invoke(self.bot.get_command('leave'))
                        print("This bot needs her beauty sleep! (timed out due to inactivity)")
                        await self._ctx.send(content='I\'m sleepy!', delete_after=30)
                    return
            self.current.data.volume = self._volume
            source = await YTDLSource.create_source(self._ctx, self.current.data.data['webpage_url'])
            self.voice.play(source, after=self.play_next_song)
            await self.current.data.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context) -> VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state
        
        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels.")

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send(f'An error occurred: {str(error)}')

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination: discord.VoiceChannel = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.

        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError(
                'You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect', 'fuckoff', 'goaway'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send(f'Volume of the player set to {volume}%')

    @commands.command(name='now', aliases=['current', 'playing', 'np'])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""
        
        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if not ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip', aliases=['no'])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter: discord.Member = ctx.message.author
        if voter == ctx.voice_state.current.requester: #! or voter.permissions_in():
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send(f'Skip vote added, currently at **{total_votes}/3**')

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.

        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += f'`{i+1}.` [**{song.source.title}**]({song.source.url})\n'

        embed = (discord.Embed(description=f'**{len(ctx.voice_state.songs)} tracks:**\n\n{queue}')
                 .set_footer(text=f'Viewing page {page}/{pages}'))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.

        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.

        If there are songs in the queue, this will be queued until the
        other songs finished playing.

        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                sources = await YTDLSource.get_info(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send(f'An error occurred while processing this request: {str(e)}')
            else:
                for song in sources:
                    print('putting', song.data.get('title'))
                    song = Song(song, requester=ctx.author)
                    await ctx.voice_state.songs.put(song)
                
                if len(sources) == 1:
                    await ctx.send(f'Enqueued {str(sources[0])}')
                else:
                    await ctx.send(f'Enqueued {len(sources)} songs')

    @commands.command(name='test')
    async def _test(self, ctx: commands.Context, testing=None):
        """quick shortcut to test playback"""

        if testing == None:
            await ctx.invoke(self._play, search="https://www.youtube.com/watch?v=8xwt0uTKSC0")

        if testing == "playlist":
            await ctx.invoke(self._play, search="https://www.youtube.com/playlist?list=OLAK5uy_l1zOAMjxnu3OE8lbtqsItSwRR2LZjIQD0")

    @commands.command(name='witch')
    async def _witch(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        ffmpeg_source = discord.FFmpegPCMAudio(
            "cum.mp3",
            **YTDLSource.FFMPEG_OPTIONS
        )
        data = {
            'uploader': 'Me',
            'uploader_url': "https://example.com",
            'upload_date': ':)',
            'title': "Fucker",
            'thumbnail': "https://circle-strafe-2001.neocities.org/don't%20ask.gif",
            'url': "https://example.com",
            'duration': 4444,
        }
        
        source = YTDLSource(ctx, ffmpeg_source, data=data)


        song = Song(source)
        await ctx.voice_state.songs.put(song)

        await ctx.send("Enqueued a banger")

    @_join.before_invoke
    @_play.before_invoke
    @_test.before_invoke
    @_witch.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError(
                'You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError(
                    'Bot is already in a voice channel.')
