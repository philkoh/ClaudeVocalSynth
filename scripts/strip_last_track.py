"""Strip the last (truncated) MTrk chunk by clipping the file at its start and
decrementing the header ntracks count. Output is a structurally valid SMF
containing only the surviving tracks."""
import struct
import sys


def main(in_path: str, out_path: str) -> None:
    with open(in_path, "rb") as f:
        buf = bytearray(f.read())
    assert buf[:4] == b"MThd"
    hdr_len = struct.unpack(">I", buf[4:8])[0]
    fmt, ntrk, division = struct.unpack(">HHH", buf[8 : 8 + hdr_len])
    pos = 8 + hdr_len
    chunks = []
    while pos < len(buf):
        if buf[pos : pos + 4] != b"MTrk":
            nxt = buf.find(b"MTrk", pos)
            if nxt < 0:
                break
            pos = nxt
            continue
        claimed = struct.unpack(">I", buf[pos + 4 : pos + 8])[0]
        chunks.append((pos, claimed))
        pos += 8 + claimed
    # find the last chunk whose claimed_len exceeds remaining
    keep_until = len(buf)
    kept_n = len(chunks)
    for i in range(len(chunks) - 1, -1, -1):
        cpos, clen = chunks[i]
        end = cpos + 8 + clen
        if end > len(buf):
            keep_until = cpos
            kept_n = i
        else:
            break
    out = bytearray(buf[:keep_until])
    out[10:12] = struct.pack(">H", kept_n)  # ntracks lives at MThd offset +2 = 8+2
    with open(out_path, "wb") as f:
        f.write(out)
    print(f"kept {kept_n}/{len(chunks)} tracks, size={len(out)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
