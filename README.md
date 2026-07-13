# Trainerfy

Trainerfy is a small audio-fingerprinting project inspired by Shazam, and based on the paper 'An Industrial-Strength Audio Search Algorithm' by Avery Li-Chun Wang. It records a short audio sample, extracts frequency-domain fingerprints, and compares them against a locally generated song database to identify the most likely matching track.

The project consists of a Python and Flask backend for audio processing and a React frontend for recording and displaying results.

> This is an experimental portfolio project rather than a production-ready music-identification service.

## Features

* Records audio directly from the browser
* Converts recorded audio into a consistent format using FFmpeg
* Extracts spectral peaks from audio
* Generates compact audio fingerprints
* Stores fingerprints in a local SQLite database
* Matches short recordings against indexed songs
* Displays the most likely song match through a web interface
* Runs entirely locally

## How it works

Trainerfy follows a simplified audio-fingerprinting pipeline:

```text
Reference songs
    ↓
Audio preprocessing
    ↓
Spectrogram generation
    ↓
Spectral peak extraction
    ↓
Fingerprint generation
    ↓
SQLite fingerprint database
```

When identifying a song:

```text
Browser recording
    ↓
Flask API
    ↓
FFmpeg conversion
    ↓
Fingerprint extraction
    ↓
Database matching
    ↓
Best matching song
```

The generated fingerprints are based on relationships between prominent frequency peaks. This allows a short recording to be compared against previously indexed songs without directly comparing the complete audio waveform.

## Technology

### Backend

* Python
* Flask
* Flask-CORS
* NumPy
* SciPy
* librosa
* Matplotlib
* Mutagen
* SQLite
* FFmpeg

### Frontend

* React
* Vite
* JavaScript
* CSS
* Browser MediaRecorder API

## Project structure

```text
trainerfy/
├── trainerfy-backend/
│   ├── databuilder.py
│   ├── fingerprinter.py
│   ├── main.py
│   ├── matcher.py
│   └── requirements.txt
│
├── trainerfy-frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

## Requirements

Before running Trainerfy, install:

* Python 3.10 or newer
* Node.js and npm
* FFmpeg

FFmpeg is a system dependency and is not installed through `requirements.txt`.

### Install FFmpeg

#### Fedora or Nobara

```bash
sudo dnf install ffmpeg
```

#### Ubuntu or Debian

```bash
sudo apt install ffmpeg
```

#### macOS

```bash
brew install ffmpeg
```

#### Windows

Install FFmpeg and add its `bin` directory to the Windows `PATH`.

Confirm that it is available:

```bash
ffmpeg -version
```

## Installation

Clone the repository:

```bash
git clone git@github.com:trainur/trainerfy.git
cd trainerfy
```

### Backend setup

Enter the backend directory:

```bash
cd trainerfy-backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend setup

From the repository root:

```bash
cd trainerfy-frontend
npm install
```

## Building the song database

Trainerfy must generate fingerprints for a local collection of reference songs before it can identify them.

By default, Trainerfy loads .mp3 files from:

~/Music

Create the database from the backend directory:

```bash
python databuilder.py --new
```

Then index the music files:

```bash
python databuilder.py --build
```

A different music directory can be optionally supplied:

```bash
python databuilder.py --build --directory "/path/to/music"
```

The available database commands can be displayed with:

```bash
python databuilder.py --help
```

Using an audio tag editor such as MusicBrainz Picard, Mp3tag, or Kid3 is recommended so that title, artist, album, and artwork metadata can be stored and displayed correctly.

The generated fingerprint database is local and is not included in this repository.

Do not commit copyrighted music files or generated databases to the repository.

## Running the application

### Start the backend

From `trainerfy-backend`:

```bash
python main.py
```

By default, the Flask server should be available at:

```text
http://localhost:5000
```

### Start the frontend

In a separate terminal:

```bash
cd trainerfy-frontend
npm run dev
```

Vite will display the local frontend address, normally:

```text
http://localhost:5173
```

Open that address in a browser.

## Usage

1. Start the Flask backend.
2. Start the React frontend.
3. Open the frontend in your browser.
4. Begin music identification and allow microphone access when prompted.
5. Keep playing the audio clip until recording is complete, and identification begins.
6. Trainerfy will compare the sample against the local fingerprint database and return the strongest match.

Identification quality depends on:

* recording length
* background noise
* microphone quality
* how many fingerprints were generated
* whether the reference recording exists in the database
* differences between live, remastered, sped-up, or compressed versions

## Development checks

Run the frontend linter:

```bash
cd trainerfy-frontend
npm run lint
```

Create a production frontend build:

```bash
npm run build
```

## Privacy

Audio recordings are sent only to the locally running Flask backend for identification. Trainerfy does not upload recordings, fingerprints, or song metadata to an external service.

The application is intended for local development and experimentation.

## Known limitations

* Identification is limited to songs already added to the local database.
* Matching may be unreliable with very short or noisy recordings.
* Different edits or live versions may not match the indexed recording.
* Database generation may take time for large music collections.
* The Flask development server is not intended for public production deployment.
* The project currently uses a simplified fingerprinting and ranking approach.

## Background

Trainerfy was created as a short personal project based on Avery Li-Chun Wang’s paper, An Industrial-Strength Audio Search Algorithm. The paper presents an elegant and approachable method for identifying recordings through sparse time-frequency landmarks and fingerprint matching.

I'd highly recommend the paper to anyone interested in audio processing, information retrieval, or implementing a music-identification system themselves, and even more so to try implementing the techniques in the paper yourself!

The project has provided experience with:

* Fourier transforms and spectrograms
* audio feature extraction
* database design
* approximate matching
* Python web APIs
* browser audio recording
* React frontend development

## Disclaimer

Trainerfy is an educational project inspired by the general concept of audio fingerprinting. It is not affiliated with, endorsed by, or connected to Shazam or Apple.

No copyrighted music is distributed with this repository.
