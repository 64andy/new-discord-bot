## Required permissions:
- Read messages
- Send messages
- Embed links
- Use external emojis
- Connect
- Speak

## Setup:
**Required:**
- FFMPEG (either on path, or in the folder. Folder works best)
- Python 3.7 or above
**Steps:**
### First Time:
1. Create a virtual environment with `python3 -m venv venv`
2. Activate the virtual environment
  - Windows: `> venv\scripts\activate.bat`
  - Linux/Mac: `$ source ./venv/scripts/activate`
3. Install dependencies with `pip install -r requirements.txt`
4. Make sure your .env file is in order (see [env](env))
### Running:
1. Activate the venv
  - Windows: `> venv\scripts\activate.bat`
  - Linux: `$ source ./venv/scripts/activate`
2. To run: `python3 -m "src"`
