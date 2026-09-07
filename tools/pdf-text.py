# -*- coding: utf-8 -*-
"""Extracteur de texte PDF minimal — zlib + operateurs Tj/TJ.

pdfminer et pypdf refusent de s'importer ici (le module cryptography du
systeme est casse : PanicException dans son binding Rust). Ces PDF de
reglementation ne sont pas chiffres, donc on n'a besoin ni de l'un ni de
l'autre : decompresser les flux FlateDecode et lire les chaines suffit.
"""
import re, sys, zlib

def streams(data):
    for m in re.finditer(rb"stream\r?\n", data):
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        raw = data[start:end].rstrip(b"\r\n")
        try:
            yield zlib.decompress(raw)
        except zlib.error:
            continue

OCT = {b"n": "\n", b"r": "\r", b"t": "\t", b"b": "", b"f": "",
       b"(": "(", b")": ")", b"\\": "\\"}

def unescape(b):
    out, i = [], 0
    while i < len(b):
        c = b[i:i+1]
        if c == b"\\" and i + 1 < len(b):
            nxt = b[i+1:i+2]
            if nxt in OCT:
                out.append(OCT[nxt]); i += 2; continue
            if nxt.isdigit():
                j = i + 1
                while j < len(b) and j < i + 4 and b[j:j+1].isdigit():
                    j += 1
                out.append(chr(int(b[i+1:j], 8))); i = j; continue
            i += 2; continue
        out.append(c.decode("latin-1")); i += 1
    return "".join(out)

def cmaps(data):
    """La table ToUnicode : le texte est en identifiants de glyphes, pas en
    caracteres. Sans elle, « Esturgeon » sort en <002800560057...>."""
    table = {}
    for dec in streams(data):
        if b"beginbfchar" not in dec and b"beginbfrange" not in dec:
            continue
        for m in re.finditer(rb"<([0-9A-Fa-f]{4})>\s*<([0-9A-Fa-f]{4,})>", dec):
            src, dst = int(m.group(1), 16), m.group(2).decode()
            table[src] = "".join(chr(int(dst[i:i+4], 16)) for i in range(0, len(dst), 4))
        for m in re.finditer(rb"<([0-9A-Fa-f]{4})>\s*<([0-9A-Fa-f]{4})>\s*<([0-9A-Fa-f]{4,})>",
                             dec):
            a, b = int(m.group(1), 16), int(m.group(2), 16)
            base = int(m.group(3)[:4], 16)
            for k in range(a, b + 1):
                table.setdefault(k, chr(base + k - a))
    return table


def hex_text(content, table):
    """Les chaines hexadecimales <....> traduites par la table."""
    out = []
    for m in re.finditer(rb"<([0-9A-Fa-f]+)>\s*Tj|T\*|ET|Td", content):
        if m.group(1) is None:
            out.append(" ")
            continue
        h = m.group(1).decode()
        out.append("".join(table.get(int(h[i:i+4], 16), "") for i in range(0, len(h), 4)))
    return "".join(out)


def text_of(content):
    out = []
    for m in re.finditer(rb"\[(.*?)\]\s*TJ|\((.*?)\)\s*Tj|T\*|ET", content, re.S):
        if m.group(1) is not None:
            parts = re.findall(rb"\((?:\\.|[^\\()])*\)", m.group(1), re.S)
            out.append("".join(unescape(p[1:-1]) for p in parts))
        elif m.group(2) is not None:
            out.append(unescape(m.group(2)))
        else:
            out.append("\n")
    return "".join(out)

def extract(path):
    data = open(path, "rb").read()
    table = cmaps(data)
    if table:
        return "\n".join(hex_text(s, table) for s in streams(data) if b"Tj" in s)
    return "\n".join(text_of(s) for s in streams(data))

if __name__ == "__main__":
    txt = extract(sys.argv[1])
    # PDFLatin1 -> les accents sortent en octal, deja convertis; on nettoie
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    print(txt)
