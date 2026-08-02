#!/usr/bin/env python3
"""
append_docx_section.py — append styled paragraphs to an existing .docx.

Used to fold the July-2026 feature work into the shipped manuals without
reflowing or reformatting the rest of the document: we unzip, insert new
<w:p> elements immediately before the final <w:sectPr>, and rezip. Existing
XML is untouched byte-for-byte, so images, numbering and the TOC field all
survive (Word refreshes the TOC on open).

Content is supplied as a list of (style, text) pairs; style is any style id
already present in the target document (Heading1/2/3, BodyText, Normal,
ListBullet, SourceCode, …), so the appended matter inherits the document's
own look rather than importing a foreign one.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def esc(t: str) -> str:
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def para(style: str, text: str, bold: bool = False) -> str:
    """One <w:p>. Bold is applied as a run property, not a style override."""
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    if not text:
        return f"<w:p>{ppr}</w:p>"
    return (f"<w:p>{ppr}<w:r>{rpr}"
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def append_section(docx_path: Path, blocks: list[tuple[str, str]]) -> None:
    """blocks: (style, text). Style '' → default paragraph."""
    tmp = Path(tempfile.mkdtemp())
    try:
        with zipfile.ZipFile(docx_path) as z:
            z.extractall(tmp)
        doc = tmp / "word" / "document.xml"
        xml = doc.read_text(encoding="utf-8")

        new_xml = "".join(para(s, t) for s, t in blocks)

        # Insert before the LAST sectPr (the body-level section properties).
        m = None
        for m in re.finditer(r"<w:sectPr[ >]", xml):
            pass
        if m is None:
            xml = xml.replace("</w:body>", new_xml + "</w:body>")
        else:
            xml = xml[:m.start()] + new_xml + xml[m.start():]

        doc.write_text(xml, encoding="utf-8")

        out = docx_path.with_suffix(".docx.tmp")
        if out.exists():
            out.unlink()
        # Deterministic rezip: mimetype-free OOXML, plain deflate is fine.
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(tmp.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(tmp).as_posix())
        shutil.move(str(out), str(docx_path))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print(__doc__)
