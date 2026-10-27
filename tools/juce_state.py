"""JUCE plugin state <-> bytes: the "VC2!" XML wrapper and JUCE's MemoryBlock base64 variant.

JUCE encodes blobs as "<size>.<chars>", 6 bits per char from the table below, packed LSB-first.
Used to read and write Arturia V Collection plugin states through pedalboard's raw_state.
"""
import re
import struct

TABLE = ".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+"
INDEX = {c: i for i, c in enumerate(TABLE)}


def juce_b64decode(s):
    size, chars = s.split(".", 1)
    out = bytearray(int(size))
    pos = 0
    for ch in chars:
        v = INDEX[ch]
        for b in range(6):
            if (v >> b) & 1 and pos + b < len(out) * 8:
                out[(pos + b) // 8] |= 1 << ((pos + b) % 8)
        pos += 6
    return bytes(out)


def juce_b64encode(data):
    bits = len(data) * 8
    chars = []
    for pos in range(0, bits, 6):
        v = 0
        for b in range(6):
            p = pos + b
            if p < bits and (data[p // 8] >> (p % 8)) & 1:
                v |= 1 << b
        chars.append(TABLE[v])
    return f"{len(data)}.{''.join(chars)}"


def unwrap(raw_state):
    """pedalboard raw_state (VC2! + XML) -> (xml text, component bytes)."""
    assert raw_state[:4] == b"VC2!", raw_state[:4]
    n = struct.unpack("<I", raw_state[4:8])[0]
    xml = raw_state[8:8 + n].rstrip(b"\0").decode()
    comp = re.search(r"<IComponent>([^<]*)</IComponent>", xml).group(1)
    return xml, juce_b64decode(comp)


def rewrap(xml, component):
    xml = re.sub(r"<IComponent>[^<]*</IComponent>", f"<IComponent>{juce_b64encode(component)}</IComponent>", xml)
    body = xml.encode() + b"\0"
    return b"VC2!" + struct.pack("<I", len(body)) + body
