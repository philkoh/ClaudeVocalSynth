"""Standalone WASAPI loopback recorder. Runs as a subprocess so COM init doesn't
conflict with the pywinauto host. Writes raw float32 PCM frames to stdout until
SIGTERM, or writes WAV to --out and stops after --seconds."""
import argparse
import sys
import time
import wave

import numpy as np
import soundcard as sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output WAV file")
    ap.add_argument("--seconds", type=float, required=True, help="Total recording duration")
    ap.add_argument("--sr", type=int, default=44100)
    args = ap.parse_args()

    spk = sc.default_speaker()
    mic = sc.get_microphone(spk.name, include_loopback=True)
    print(f"[rec] loopback from {spk.name!r} for {args.seconds:.1f}s", flush=True)
    chunks = []
    with mic.recorder(samplerate=args.sr, channels=2, blocksize=1024) as r:
        start = time.time()
        while time.time() - start < args.seconds:
            data = r.record(numframes=2048)
            chunks.append(data)
    audio = np.concatenate(chunks) if chunks else np.zeros((0, 2), dtype=np.float32)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    rms = float(np.sqrt(np.mean(audio ** 2))) if audio.size else 0.0
    print(f"[rec] captured {audio.shape[0]/args.sr:.2f}s, peak={peak:.4f}, rms={rms:.4f}", flush=True)
    pcm = (audio * 32767).clip(-32767, 32767).astype(np.int16)
    with wave.open(args.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(args.sr)
        w.writeframes(pcm.tobytes())
    print(f"[rec] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
