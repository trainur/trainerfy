from flask import Flask, jsonify, request
from flask_cors import CORS
from collections import defaultdict
import tempfile
import subprocess
import librosa
import fingerprinter
import matcher

app = Flask(__name__)
CORS(app)


COUNT_THRESHOLD = 8
QUANTIZE_DIFF = 4

def convert_to_wav(input_path):
    output_path = input_path + ".wav"
    subprocess.run([
        "ffmpeg", "-v", "quiet", "-y",
        "-i", input_path,
        "-af", "loudnorm",
        "-ar", "22050",
        "-ac", "1",
        output_path
    ], check=True)
    return output_path

@app.route("/identify", methods=["POST"])
def identify():
    audio_data = request.data

    app.logger.info(f"Received audio data of length: {len(audio_data)} bytes")

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
        temp_file.write(audio_data)
        temp_file.flush()
        audio_path = temp_file.name

    audio_path = convert_to_wav(audio_path)

    with open(audio_path, "rb") as src:
        with open("debug_audio.wav", "wb") as dst:
            dst.write(src.read())

    audio, sr = librosa.load(audio_path, sr=22050)
    app.logger.info(f"Duration: {len(audio)/sr:.2f}s")
    app.logger.info(f"Max amplitude: {audio.max():.4f}")

    app.logger.debug(f"Saved audio data to temporary file: {audio_path}")

    fingerprint = fingerprinter.generate_song_fingerprint(audio_path)

    app.logger.info(f"Generated fingerprint with {len(fingerprint)} hashes")
    app.logger.debug(f"Query times spread: min={min(t for h,t in fingerprint)}, max={max(t for h,t in fingerprint)}, unique={len(set(t for h,t in fingerprint))}")

    bins = defaultdict(list)

    for h, t in fingerprint:
        matches = matcher.find_associated_fingerprints(h)
        if not matches: continue
        for (id, t_m) in matches:
            diff = round(t - t_m)
            diff_quantised = round(diff / QUANTIZE_DIFF) * QUANTIZE_DIFF
            bins[(id, diff_quantised)].append((h, t, t_m))

    app.logger.info(f"Total unique bins: {len(bins)}")
    app.logger.info(f"Total matches across all bins: {sum(len(v) for v in bins.values())}")

    # Show top 5 bins
    top_bins = sorted(bins.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    for (song_id, diff), pairs in top_bins:
        app.logger.info(f"  song_id={song_id}, diff={diff}, count={len(pairs)}")

    if not bins: return jsonify({"success": False})

    best_key, best_pairs = top_bins[0]
    best_song_id, best_diff = best_key
    best_count = len(best_pairs)

    app.logger.info(
        f"Best bin: song_id={best_song_id}, diff={best_diff}, count={best_count}"
    )

    if best_count < COUNT_THRESHOLD:
        app.logger.info(f"Best count {best_count} is below threshold {COUNT_THRESHOLD}, returning no match")
        return jsonify({"success": False})

    id, title, artist, album, artwork, artwork_mime = matcher.fetch_song(best_song_id)

    app.logger.debug(f"Fetched song id: {id}")

    return jsonify({    
        "success": True,
        "title": title,
        "artist": artist,
        "album": album,
        "artwork": artwork,
        "artwork_mime": artwork_mime
    })

if __name__ == "__main__":
    app.run(debug=True)