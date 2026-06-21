"""
submission/make_pptx.py: build a real .pptx pitch deck (accepted Presentation format)
from PITCH_DECK.md, embedding the generated figures on the relevant slides and putting
the speaker notes in each slide's notes pane.

Run:  pip install python-pptx && python submission/make_pptx.py
"""
from __future__ import annotations
import os
import re

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
ACCENT = RGBColor(0xE4, 0x57, 0x2E)
INK = RGBColor(0x1B, 0x2A, 0x4A)
GREY = RGBColor(0x55, 0x5F, 0x70)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# figure per slide number
FIGS = {5: "fig-concentration.png", 6: "fig-map.png", 8: "fig-forecast.png",
        9: "fig-coverage.png", 10: "fig-gap.png", 11: "fig-pipeline.png"}

clean = lambda s: re.sub(r"[*`]", "", s).strip()


def parse_slides(md):
    text = open(md, encoding="utf-8").read()
    out = []
    for block in re.split(r"\n(?=### )", text):
        lines = block.strip().splitlines()
        if not lines or not lines[0].startswith("### "):
            continue
        num, _, title = lines[0][4:].strip().partition(". ")
        bullets, notes = [], ""
        for ln in lines[1:]:
            ln = ln.rstrip()
            if ln.startswith("- "):
                bullets.append(clean(ln[2:]))
            elif ln.startswith("> Speaker:"):
                notes = ln[len("> Speaker:"):].strip()
            elif ln.startswith("> ") or ln.startswith("*Visual:*") or ln in ("", "---"):
                continue
            elif not ln.startswith(("**ParkPulse**", "Find the parking", "Team Spectres", "Demo:")):
                bullets.append(clean(ln))
        out.append({"num": num, "title": title, "bullets": bullets, "notes": notes})
    return out


def accent_bar(slide, prs):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.16))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()


def textbox(slide, l, t, w, h):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    return tb.text_frame


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # title slide
    s = prs.slides.add_slide(blank)
    accent_bar(s, prs)
    tf = textbox(s, 0.9, 2.1, 11.5, 3.5)
    for txt, size, color, bold in [
        ("ParkPulse", 60, ACCENT, True),
        ("Find the parking that actually chokes traffic, and patrol it first.", 24, INK, False),
        ("Gridlock Hackathon 2.0 (Flipkart), Round 2  |  Poor Visibility on Parking-Induced Congestion", 14, GREY, False),
        ("Team Spectres  ·  Kavya Mahajan, Aarav Harshvardhan, Souhardyo Dasgupta, Vishesh Gupta", 16, INK, True),
        ("Demo: https://flipkart-gridlock-gamma.vercel.app/", 14, ACCENT, False),
    ]:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = txt; p.font.size = Pt(size); p.font.color.rgb = color; p.font.bold = bold
        p.space_after = Pt(10)

    for sl in parse_slides(os.path.join(HERE, "PITCH_DECK.md")):
        if sl["num"] == "1":
            continue  # custom title slide above
        s = prs.slides.add_slide(blank)
        accent_bar(s, prs)
        has_fig = int(sl["num"]) in FIGS and os.path.exists(os.path.join(FIGDIR, FIGS[int(sl["num"])]))
        # title
        tt = textbox(s, 0.6, 0.5, 12, 1.0)
        p = tt.paragraphs[0]; p.text = sl["title"]; p.font.size = Pt(30); p.font.bold = True; p.font.color.rgb = INK
        # bullets
        body_w = 6.6 if has_fig else 11.8
        bf = textbox(s, 0.7, 1.7, body_w, 5.2)
        first = True
        for b in sl["bullets"]:
            p = bf.paragraphs[0] if first else bf.add_paragraph()
            first = False
            p.text = "•  " + b; p.font.size = Pt(19); p.font.color.rgb = INK; p.space_after = Pt(12)
        # figure
        if has_fig:
            s.shapes.add_picture(os.path.join(FIGDIR, FIGS[int(sl["num"])]),
                                 Inches(7.5), Inches(1.8), width=Inches(5.3))
        # speaker notes
        if sl["notes"]:
            s.notes_slide.notes_text_frame.text = sl["notes"]

    out = os.path.join(HERE, "ParkPulse_Pitch_Deck.pptx")
    prs.save(out)
    print(f"wrote {out} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
