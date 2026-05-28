"""Final mix step (run after vocal WAV is exported from Synth V).

Usage: python mix.py vocal.wav backing.wav out.mp3
- vocal starts at the same absolute time as the .svp's first note (~32.5s into the
  song); ffmpeg amix handles alignment because both vocal and backing share the
  same absolute timeline (vocal's silence before note 1 ≈ backing's intro).
- Vocal gain set slightly higher than backing for typical mix balance.
"""
import subprocess
import sys

FFMPEG = r"C:\Tools\ffmpeg\bin\ffmpeg.exe"


def main(vocal: str, backing: str, out: str) -> None:
    cmd = [
        FFMPEG,
        "-y",
        "-i", vocal,
        "-i", backing,
        "-filter_complex",
        "[0:a]volume=1.6[v];[1:a]volume=0.9[b];[v][b]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=0.98",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        out,
    ]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
