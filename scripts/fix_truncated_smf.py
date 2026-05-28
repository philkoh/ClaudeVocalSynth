"""Fix an SMF whose final MTrk chunk's claimed length overshoots the file by N bytes.
Rewrites the last chunk header to the actual remaining size, and appends 00 FF 2F 00
(delta=0, End-of-Track) so mido can parse cleanly.
"""
import struct
import sys


def main(in_path: str, out_path: str) -> None:
    with open(in_path, "rb") as f:
        buf = bytearray(f.read())
    if buf[:4] != b"MThd":
        raise SystemExit("not SMF")
    hdr_len = struct.unpack(">I", buf[4:8])[0]
    pos = 8 + hdr_len
    last_hdr_pos = None
    while pos < len(buf):
        if buf[pos : pos + 4] != b"MTrk":
            nxt = buf.find(b"MTrk", pos)
            if nxt < 0:
                break
            pos = nxt
            continue
        claimed = struct.unpack(">I", buf[pos + 4 : pos + 8])[0]
        last_hdr_pos = pos
        pos += 8 + claimed
    if last_hdr_pos is None:
        raise SystemExit("no MTrk found")
    actual = len(buf) - (last_hdr_pos + 8)
    # Append an End-of-Track if we don't already end at one
    tail = bytes([0x00, 0xFF, 0x2F, 0x00])
    if not buf.endswith(tail):
        buf += tail
        actual += 4
    buf[last_hdr_pos + 4 : last_hdr_pos + 8] = struct.pack(">I", actual)
    with open(out_path, "wb") as f:
        f.write(buf)
    print(f"patched: last MTrk new_len={actual}, file_size={len(buf)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
