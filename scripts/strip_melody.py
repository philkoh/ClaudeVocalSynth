"""Drop the 'melody' track from the .kar so we have an instrument-only backing MIDI."""
import sys
import mido


def main(in_path: str, out_path: str, drop_substr: str = "melody") -> None:
    src = mido.MidiFile(in_path, clip=True)
    out = mido.MidiFile(type=src.type, ticks_per_beat=src.ticks_per_beat)
    dropped = []
    for i, tr in enumerate(src.tracks):
        name = None
        for msg in tr:
            if msg.type == "track_name":
                name = msg.name
                break
        if name and drop_substr.lower() in name.lower():
            dropped.append((i, name))
            continue
        out.tracks.append(tr)
    out.save(out_path)
    print(f"wrote {out_path}: kept {len(out.tracks)} tracks, dropped {dropped}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
