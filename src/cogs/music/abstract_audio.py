# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Optional
from discord import AudioSource, Embed


class AbstractAudio(ABC):
    """
    An abstraction layer that provides data about a given audio, and allows lazy loading of audio sources.
    """

    @abstractmethod
    async def generate_source(self) -> AudioSource:
        ...

    @abstractmethod
    def create_embed(self) -> Embed:
        ...

    def short_audio_info(self) -> str:
        name = self.name
        url = self.url
        if self.url is None:
            info_str = f"**{name}**"
        else:
            info_str = f"[**{name}**]({url})"

        return f"{info_str} - {self.parse_duration()}"

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def url(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def length(self) -> Optional[int]:
        ...

    def parse_duration(self) -> str:
        total_length = int(self.length)
        if total_length is None:
            return "unkn length"
        minutes, seconds = divmod(total_length, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        total_length = []
        if days > 0:
            total_length.append(f"{days}d")
        if hours > 0:
            total_length.append(f"{hours}h")
        if minutes > 0:
            total_length.append(f"{minutes}m")
        if seconds > 0:
            total_length.append(f"{seconds}s")

        return " ".join(total_length)
