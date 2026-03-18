#!/usr/bin/env python3
"""
Wren's Audio Analysis MCP Server

Gives Wren ears. Accepts YouTube URLs or local file paths,
extracts audio features using librosa, returns structured data.

Tools:
  - analyze_track: Full analysis (BPM, key, energy, beats, spectral)
  - get_energy_curve: Energy/loudness over time
  - get_frequency_bands: Bass/mid/treble levels over time
  - download_audio: Download YouTube URL to local mp3

Setup:
  conda activate wren-audio
  python server.py
"""

import json
import os
import tempfile
import hashlib
from pathlib import Path

import librosa
import numpy as np
import yt_dlp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Cache directory for downloaded audio
CACHE_DIR = Path(tempfile.gettempdir()) / "wren-audio-cache"
CACHE_DIR.mkdir(exist_ok=True)

server = Server("wren-audio")


# --- Helpers ---

def url_to_cache_path(url: str) -> Path:
    """Generate a cache path for a URL."""
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    return CACHE_DIR / f"{h}.mp3"


def download_youtube(url: str) -> tuple[str, str]:
    """Download YouTube audio to mp3, returns (file_path, title)."""
    cache_path = url_to_cache_path(url)
    if cache_path.exists():
        return str(cache_path), "cached"

    ydl_opts = {
        'format': 'worstaudio/worst',  # smallest file = fastest download
        'outtmpl': str(cache_path.with_suffix('.%(ext)s')),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '64',  # low quality fine for analysis
        }],
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'unknown')

    # yt-dlp may save with different extension before converting
    if not cache_path.exists():
        # Try finding the file
        for f in CACHE_DIR.glob(f"{cache_path.stem}.*"):
            if f.suffix in ('.mp3', '.m4a', '.wav', '.opus', '.webm'):
                if f.suffix != '.mp3':
                    os.rename(f, cache_path)
                break

    return str(cache_path), title


def resolve_audio(source: str) -> tuple[str, str]:
    """Resolve a source (URL or path) to a local audio file path + title."""
    if source.startswith(('http://', 'https://')):
        path, title = download_youtube(source)
        return path, title
    elif Path(source).exists():
        return source, Path(source).stem
    else:
        raise ValueError(f"Cannot resolve audio source: {source}")


def analyze_audio(path: str, duration: float = 90) -> dict:
    """Run full librosa analysis on an audio file."""
    y, sr = librosa.load(path, duration=duration)
    total_duration = librosa.get_duration(y=y, sr=sr)

    # Tempo & beats
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, onset_envelope=onset_env)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    tempo_val = float(np.atleast_1d(tempo)[0])

    # Key estimation via chroma
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    mean_chroma = np.mean(chroma, axis=1)
    key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    estimated_key = key_names[int(np.argmax(mean_chroma))]

    # Major/minor estimation (simplified)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    # Rotate profiles to match detected key
    key_idx = int(np.argmax(mean_chroma))
    major_corr = np.corrcoef(mean_chroma, np.roll(major_profile, key_idx))[0, 1]
    minor_corr = np.corrcoef(mean_chroma, np.roll(minor_profile, key_idx))[0, 1]
    mode = "major" if major_corr > minor_corr else "minor"

    # Energy (RMS) — downsampled to ~1 per second
    rms = librosa.feature.rms(y=y)[0]
    hop = max(1, len(rms) // int(total_duration))
    energy_curve = rms[::hop].tolist()[:int(total_duration)]
    avg_energy = float(np.mean(rms))
    max_energy = float(np.max(rms))

    # Spectral features
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    avg_brightness = float(np.mean(centroid))
    avg_rolloff = float(np.mean(rolloff))

    # Frequency bands (approximate bass/mid/treble)
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    bass_mask = freqs < 250
    mid_mask = (freqs >= 250) & (freqs < 4000)
    treble_mask = freqs >= 4000
    bass_energy = float(np.mean(S[bass_mask, :])) if bass_mask.any() else 0
    mid_energy = float(np.mean(S[mid_mask, :])) if mid_mask.any() else 0
    treble_energy = float(np.mean(S[treble_mask, :])) if treble_mask.any() else 0
    # Normalize to 0-1
    band_max = max(bass_energy, mid_energy, treble_energy, 0.001)
    bass_norm = bass_energy / band_max
    mid_norm = mid_energy / band_max
    treble_norm = treble_energy / band_max

    # Onset density (how "busy" the track is)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    onset_density = len(onsets) / total_duration  # onsets per second

    # Silence ratio
    silence_threshold = 0.01 * max_energy
    silence_frames = np.sum(rms < silence_threshold)
    silence_ratio = float(silence_frames / len(rms))

    # Mood estimation (simple heuristic)
    if avg_energy > 0.15 and tempo_val > 120:
        mood = "energetic"
    elif avg_energy < 0.05 and silence_ratio > 0.2:
        mood = "ambient"
    elif mode == "minor" and avg_energy < 0.1:
        mood = "melancholy"
    elif mode == "minor" and avg_energy >= 0.1:
        mood = "intense"
    elif mode == "major" and avg_energy > 0.1:
        mood = "uplifting"
    else:
        mood = "neutral"

    return {
        "duration_seconds": round(total_duration, 2),
        "tempo_bpm": round(tempo_val, 1),
        "estimated_key": f"{estimated_key} {mode}",
        "beat_count": len(beat_times),
        "beat_times_seconds": [round(t, 3) for t in beat_times[:50]],  # first 50
        "energy": {
            "average": round(avg_energy, 4),
            "max": round(max_energy, 4),
            "curve_per_second": [round(e, 4) for e in energy_curve],
        },
        "frequency_bands": {
            "bass": round(bass_norm, 3),
            "mid": round(mid_norm, 3),
            "treble": round(treble_norm, 3),
        },
        "spectral": {
            "brightness_hz": round(avg_brightness, 1),
            "rolloff_hz": round(avg_rolloff, 1),
        },
        "rhythm": {
            "onset_density_per_second": round(onset_density, 2),
            "beat_regularity": round(float(np.std(np.diff(beat_times))) if len(beat_times) > 2 else 0, 4),
        },
        "silence_ratio": round(silence_ratio, 3),
        "estimated_mood": mood,
    }


def get_bands_over_time(path: str, resolution: int = 50) -> dict:
    """Get bass/mid/treble levels over time."""
    y, sr = librosa.load(path)
    duration = librosa.get_duration(y=y, sr=sr)

    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    bass_mask = freqs < 250
    mid_mask = (freqs >= 250) & (freqs < 4000)
    treble_mask = freqs >= 4000

    n_frames = S.shape[1]
    hop = max(1, n_frames // resolution)

    bass = [float(np.mean(S[bass_mask, i:i+hop])) for i in range(0, n_frames, hop)]
    mid = [float(np.mean(S[mid_mask, i:i+hop])) for i in range(0, n_frames, hop)]
    treble = [float(np.mean(S[treble_mask, i:i+hop])) for i in range(0, n_frames, hop)]

    # Normalize
    all_max = max(max(bass), max(mid), max(treble), 0.001)
    bass = [round(v / all_max, 3) for v in bass]
    mid = [round(v / all_max, 3) for v in mid]
    treble = [round(v / all_max, 3) for v in treble]

    time_points = [round(i * duration / len(bass), 2) for i in range(len(bass))]

    return {
        "duration": round(duration, 2),
        "resolution": len(bass),
        "time_points": time_points,
        "bass": bass,
        "mid": mid,
        "treble": treble,
    }


# --- MCP Tools ---

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="analyze_track",
            description="Full audio analysis of a track. Accepts YouTube URL or local file path. Returns BPM, key, energy, beats, spectral features, frequency bands, mood estimation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "YouTube URL or local file path to analyze",
                    },
                    "max_duration": {
                        "type": "number",
                        "description": "Max seconds to analyze (default: full track). Use 60 for quick analysis.",
                    },
                },
                "required": ["source"],
            },
        ),
        Tool(
            name="get_frequency_bands",
            description="Get bass/mid/treble levels over time for a track. Returns time-series data suitable for visualization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "YouTube URL or local file path",
                    },
                    "resolution": {
                        "type": "integer",
                        "description": "Number of data points (default: 50)",
                    },
                },
                "required": ["source"],
            },
        ),
        Tool(
            name="download_audio",
            description="Download audio from YouTube URL to local cache. Returns the local file path for further analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube URL to download",
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "analyze_track":
            source = arguments["source"]
            max_dur = arguments.get("max_duration", 90)  # default 90s to avoid timeout
            path, title = resolve_audio(source)
            result = analyze_audio(path, duration=max_dur)
            result["title"] = title
            result["source"] = source
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )]

        elif name == "get_frequency_bands":
            source = arguments["source"]
            res = arguments.get("resolution", 50)
            path, title = resolve_audio(source)
            result = get_bands_over_time(path, resolution=res)
            result["title"] = title
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )]

        elif name == "download_audio":
            url = arguments["url"]
            path, title = download_youtube(url)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "path": path,
                    "title": title,
                    "url": url,
                }, indent=2),
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
