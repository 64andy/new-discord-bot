# MisakiBot - Discord Music Bot for playing your personal music library
*[Forked from vbe0201's gist](https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d)*

A small Discord bot that can:
- Play music (both from YouTube links and local files)
- Archive your pinned messages to get around the pin limit
- Make decisions & roll dice

This was created for personal use after the bigger music bots got deleted in 2021

# Required Discord permissions:
- Read messages
- Send messages
- Embed links
- Use external emojis
- Connect
- Speak

## Setup:
### Required:
- [A registered bot application on Discord](https://discord.com/developers/applications)
- FFMPEG (either on path, or in the folder. Folder works best)
- Python 3.7 or above
### Steps:
#### First Time:
1. Create a virtual environment with `python3 -m venv venv`
2. Activate the virtual environment
  - Windows: `> venv\scripts\activate.bat`
  - Linux/Mac: `$ source ./venv/scripts/activate`
3. Install dependencies with `pip install -r requirements.txt`
4. Make sure your .env file is in order (see [env](env))
#### Running:
1. Activate the venv
  - Windows: `> venv\scripts\activate.bat`
  - Linux: `$ source ./venv/scripts/activate`
2. To run: `python3 -m "src"`

---

## Commands:
### Music:
- `alexa play <YouTubeURL>` - Joins your voice channel and plays that video/playlist.
  - `YoutubeURL`: Either a YouTube video, or a YouTube playlist. If a playlist, all of its videos are queued up. 
  - If it's already playing music, the video will be queued.
- `/play-local <title?> <album?> <artist?>` - Lets you search and play music stored locally on the bot's machine.
  - **This is a slash-command (No alexa prefix)**
  - If ONLY `album` is set, the entire album is queued.
  - Otherwise, the single specified song is played.
- `alexa leave` - Stops playing music and disconnects
  - *Aliases:* `disconnect, goaway`
- `alexa now` - Displays the currently playing song
  - *Aliases:* `current, playing, np`
- `alexa queue <page?>` - Lists the next 10 songs being queued
  - `page`: (Optional) If the queue's larger than 10, you can go to a specified page
- `alexa loop` - Loops/Unloops the current song
- `alexa pause` - Pauses the current song
- `alexa resume` - Unpauses the current song
  - *Aliases:* `unpause`
- `alexa skip` - Skips the current song
  - *Aliases:* `no, next`
- `alexa stop` - Stops playing and clears the queue
- `alexa remove <index>` - Remove the specified song
  - `index`: The queue position of the song
- `alexa move <song_pos> <target_pos>` - Moves the given song queued to a new position
  - `song_pos`: The queue position of the song in question
  - `target_pos`: The queue position you want it to be
### Archiving:
**Whenever a message is pinned, it'll be added to the specified channel**
- `alexa set-archive <channel?>` - Sets either the current channel, or specified channel, as the pin archive
- `alexa remove-archive` - Pins will no longer be archived

### Decisions/misc
- `alexa 8ball <question>` - Ask a question and get an answer
  - *Aliases:* `alexa 🎱`
- `alexa coinflip` - Flip a coin, gives heads or tails
  - *Aliases:* `coin, flip`
- `alexa choose <options>` - Chooses from your comma-separated list of options
  - *Aliases:* `decide, pick`
  - e.g. `alexa choose burgers, fries` returns either "burgers" or "fries"
- `alexa roll <dice>` - Rolls a plus-separated list of dice, with a total & average.
  - `dice`: Represents the amount of, and sides of, the rolled dice.
    - e.g. `6+20+20` rolls one 6-sided die and two 20-sided die.
- `alexa d20` - Rolls a single D20

## Trouble-shooting
#### I get a `DownloadError` when trying to play a video:
- `Video unavailable`: The specified video is unavailable. Reasons for this include:
  - The video is private
  - The video isn't available in the bot host's country (e.g. The bot's being run in New Zealand, but the video's only available in the US)
- ` Unable to extract <...>`: YouTube might have changed their API. To address this, update YT-DLP with `pip install -U yt-dlp`

#### I can't search my local music
- Make sure your music folder is set in a `.env` file
- Your music is checked on bot startup. If you add/remove music, you'll need to restart the bot.
- Searching is based off your music's metadata, so ensuring all your music's got a Title, Album, and Artist set is important. To do this, I'd recommend [Mp3tag](https://www.mp3tag.de/en/)