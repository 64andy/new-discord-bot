import asyncio
import itertools
import logging
import random
from typing import Optional

import discord
from async_timeout import timeout
from discord.ext import commands

from .abstract_audio import AbstractAudio

class VoiceError(commands.CommandInvokeError):
    pass

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
    def __init__(self, bot: commands.Bot, channel: discord.TextChannel):
        self.bot = bot
        self.channel = channel

        self.current: Optional[AbstractAudio] = None
        self.voice: Optional[discord.VoiceClient] = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False

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
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self) -> None:
        try:
            while True:
                self.next.clear()

                if not self.loop:
                    # Try to get the next song within 3 minutes.
                    # If no song will be added to the queue in time,
                    # the player will disconnect due to performance
                    # reasons.
                    try:
                        async with timeout(180):  # 3 minutes
                            print("Trying to get new song")
                            self.current: AbstractAudio = await self.songs.get()
                    except asyncio.TimeoutError:
                        if self.voice:
                            print("This bot needs her beauty sleep! (timed out due to inactivity)")
                            await self.channel.send(content="I'm sleepy!", delete_after=30)
                            break   # Leave channel
                print("Got song ", self.current)
                source = await self.current.generate_source()
                self.voice.play(source, after=self.play_next_song)
                await self.channel.send(embed=self.current.create_embed())
                await self.next.wait()
        except Exception as e:
            logging.exception(e)
            await self.channel.send("Error:", e)
        finally:
            await self.stop()


    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None
