"""
Original created by vbe0201
https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
Copyright (c) 2019 Valentin B.

Modified by 64andy, 2021
"""

import logging
import math
from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from .music.abstract_audio import AbstractAudio
from .music.find_local_audio import LocalAudioLibrary
from .music.local_audio_source import LocalAudioSource
from .music.voice_state import VoiceError, VoiceState
from .music.ytdl_source import YTDLError, YTDLSource

EMPTY_QUEUE_MSG = 'Queue is empty.'

logger = logging.getLogger(__name__)

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot, music_folder: Optional[str]):
        self.bot = bot
        self.voice_states: Dict[int, VoiceState] = {}
        if music_folder is None:
            logging.warn(".env variable `LOCAL_MUSIC_FOLDER` not set. Playing local music is disabled.")
            self.local_library = None
        else:
            self.local_library = LocalAudioLibrary(music_folder)
        # Manually attach the autocomplete callbacks, because decorators
        # are processed at compile time, and local_library doesn't yet
        if self.local_library is not None:
            app_commands.autocomplete(
                title=self.local_library.get_autocomplete_suggestions('title'),
                album=self.local_library.get_autocomplete_suggestions('album'),
                artist=self.local_library.get_autocomplete_suggestions('artist')
            )(self._play_local)


    def get_voice_state(self, channel: discord.TextChannel) -> VoiceState:
        """Gets the voice state of this"""
        server_id = channel.guild.id
        state = self.voice_states.get(server_id)
        if not state or state.is_destroyed:
            state = VoiceState(self.bot, channel)
            self.voice_states[server_id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels.")
        return True

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        logger.exception(error)
        await ctx.send(f'An error occurred: {str(error)}')


    async def join_voice_channel(self, voice_state: VoiceState, command_caller: discord.Member):
        """Joins the voice channel of whoever called this"""
        if not command_caller.voice or not command_caller.voice.channel:
            raise commands.CommandError(
                'You are not connected to any voice channel.')

        vc = command_caller.voice.channel
        if not voice_state.voice or not voice_state.voice.channel:   # If we're not in a VC:
            voice_state.voice = await vc.connect()
            return
        
        await voice_state.voice.move_to(vc)

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        voice_state = self.get_voice_state(ctx.channel)
        await self.join_voice_channel(voice_state, ctx.author)


    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.

        If no channel was specified, it joins your channel.
        """
        voice_state = self.get_voice_state(ctx.channel)

        if not channel and not ctx.author.voice:
            raise VoiceError(
                'You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if voice_state.voice:
            await voice_state.voice.move_to(destination)
            return

        voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect', 'fuckoff', 'goaway'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""
        voice_state = self.get_voice_state(ctx.channel)

        if not voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='now', aliases=['current', 'playing', 'np'])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""
        voice_state = self.get_voice_state(ctx.channel)

        await ctx.send(embed=voice_state.current.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        voice_state = self.get_voice_state(ctx.channel)

        if not voice_state.is_playing and voice_state.voice.is_playing():
            voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume', aliases=['unpause'])
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""
        voice_state = self.get_voice_state(ctx.channel)

        if not voice_state.is_playing and voice_state.voice.is_paused():
            voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""
        voice_state = self.get_voice_state(ctx.channel)

        voice_state.songs.clear()

        if not voice_state.is_playing:
            voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip', aliases=['no'])
    async def _skip(self, ctx: commands.Context):
        """Skips the current song"""
        voice_state = self.get_voice_state(ctx.channel)

        if not voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')
        voice_state.skip()

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.

        You can optionally specify the page to show. Each page contains 10 elements.
        """
        voice_state = self.get_voice_state(ctx.channel)

        if len(voice_state.songs) == 0:
            return await ctx.send(EMPTY_QUEUE_MSG)

        items_per_page = 10
        pages = math.ceil(len(voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queued_songs: List[AbstractAudio] = voice_state.songs[start:end]
        queue_message = ''.join(
            f"`{i+1}.` {song.short_audio_info()}\n"
            for i, song in enumerate(queued_songs, start=start)
        )

        embed = (discord.Embed(title="Queue",
                               description=f'**{len(voice_state.songs)} tracks:**'
                               '\n'
                               '\n'
                               f'{queue_message}')
                 .set_footer(text=f'Viewing page {page}/{pages}'))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""
        voice_state = self.get_voice_state(ctx.channel)

        if len(voice_state.songs) == 0:
            return await ctx.send(EMPTY_QUEUE_MSG)

        voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""
        voice_state = self.get_voice_state(ctx.channel)

        if len(voice_state.songs) == 0:
            return await ctx.send(EMPTY_QUEUE_MSG)

        voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.

        Invoke this command again to unloop the song.
        """
        voice_state = self.get_voice_state(ctx.channel)

        if not voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        voice_state.loop = not voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.

        If there are songs in the queue, this will be queued until the
        other songs finished playing.

        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        voice_state = self.get_voice_state(ctx.channel)

        await self.join_voice_channel(voice_state, ctx.author)

        async with ctx.typing():
            try:
                audio_to_add = await YTDLSource.from_query(search, ctx.author)
            except YTDLError as e:
                await ctx.send(f'An error occurred while processing this request: {str(e)}')
            else:
                for song in audio_to_add:
                    print('putting the YT song:', song.name)
                    await voice_state.songs.put(song)
                if len(audio_to_add) > 1:
                    await ctx.send(f'Enqueued {len(audio_to_add)} songs')
                else:
                    await ctx.send(f'Enqueued song: {audio_to_add[0]}')

    @commands.command(name='test')
    async def _test(self, ctx: commands.Context, testing: str = None):
        """quick shortcut to test playback"""

        if testing == None:
            await ctx.invoke(self._play, search="https://www.youtube.com/watch?v=8xwt0uTKSC0")

        if testing == "playlist":
            await ctx.invoke(self._play, search="https://www.youtube.com/playlist?list=OLAK5uy_l1zOAMjxnu3OE8lbtqsItSwRR2LZjIQD0")

    
    @app_commands.command(name="play-local")
    @app_commands.describe(
        title="An individual song's name. If set, only the specified song will play.",
        album="The album. The entire album is queued... UNLESS `title` is set, then it's used for filtering.",
        artist="The song artist. Only used for filtering.",
    )
    async def _play_local(self, interaction: discord.Interaction, *,
        title: Optional[str]="",
        album: Optional[str]="",
        artist: Optional[str]=""
        ):
        """Plays a local song if `title` is set, or a whole album if it isn't."""
        # Has local music been set?
        if self.local_library is None:
            return await interaction.response.send_message("❌ Can't play local songs, as the bot runner hasn't set a music folder. Try the normal play command")
        # `title` or `album` need to be set       
        if not title and not album:
            if not artist:
                await interaction.response.send_message(
                    "❌ No fields were entered.\n"
                    "At minimum, the `title` or `album` fields must be entered.")
            else:
                await interaction.response.send_message(
                    "Sorry, you can't search **only** by artist.\n"
                    "At minimum, the `title` or `album` fields must be entered.")
            return

        voice_state = self.get_voice_state(interaction.channel)
        await self.join_voice_channel(voice_state, interaction.user)

        possibilities = self.local_library.find_possible_songs(title=title, album=album, artist=artist)
        if len(possibilities) == 0:
            return await interaction.response.send_message("Error: Couldn't find any songs from your search")
        
        if title:
            audio_file = possibilities[0]
            song = LocalAudioSource(audio_file, added_by=interaction.user)
            print('putting the local song:', song.name)
            MSG = f'Enqueued song: {song}'
            if len(possibilities) > 1:
                MSG = f'⚠ {len(possibilities)} possible song matches. Use the album & artist fields to filter.\n' + MSG
            await voice_state.songs.put(song)
            await interaction.response.send_message(MSG)
        elif album:
            possibilities.sort()
            n_songs = len(possibilities)
            print('putting', n_songs, "local song(s)")
            for audio_file in possibilities:
                song = LocalAudioSource(audio_file, added_by=interaction.user)
                await voice_state.songs.put(song)
            await interaction.response.send_message(f'Enqueued {n_songs} songs from **{audio_file.album}**')
        
    
    @_join.before_invoke
    @_play.before_invoke
    @_test.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError(
                'You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError(
                    'Bot is already in a voice channel.')
        

