"""Homepage AR (RTL mockup) — 1440x2400.
Note: No Arabic font available in this sandbox, so the layout is mirrored to RTL
with all content placeholders; production must render real Arabic via a Noto
Naskh Arabic font (see design/BRIEF.md).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _dmd_brand import *
from PIL import ImageOps

W, H = 1440, 2400

# Start from the FR homepage by re-running its builder in-memory, then mirror.
import _01_homepage_fr
import importlib
# Rebuild by importing
img = _01_homepage_fr.img
draw = _01_homepage_fr.draw

# Mirror horizontally (RTL = everything flipped)
mirrored = ImageOps.mirror(img)

# Add a "RTL / AR" ribbon top-right (now top-left after mirror) and re-render a
# couple of labels to make the RTL intent unambiguous. We compose onto a new
# canvas so the badge sits on top after mirroring.
canvas = Image.new("RGB", (W, H), BRAND["offwhite"])
canvas.paste(mirrored, (0, 0))
d2 = ImageDraw.Draw(canvas)

# AR mode banner across the top
d2.rectangle([0, 0, W, 36], fill=BRAND["green"])
# In RTL: text reads right-to-left
ar_msg = "✦ عرض RTL — واجهة عربية (خط Noto Naskh Arabic مطلوب في الإنتاج)"
tw, _ = text_w(d2, ar_msg, font("bold", 14))
d2.text((W - 30 - tw, 8), ar_msg, font=font("bold", 14), fill=BRAND["white"])

# Add a clearer "AR" sticker near the lang switcher (now on the left after mirror)
rounded(d2, [28, 80, 84, 110], 12, fill=BRAND["green"])
aw, _ = text_w(d2, "AR ✓", font("bold", 14))
d2.text((56 - aw / 2, 84), "AR ✓", font=font("bold", 14), fill=BRAND["white"])

# Mirror the language pill labels themselves to keep them readable as "AR EN RU ZH FR" left-to-right
# (since the original draw had FR first, the mirrored layout already has it last; good.)

out = "/root/.openclaw/workspace/dubai-medical-directory/design/homepage_AR.png"
canvas.save(out, "PNG", optimize=True)
print(f"✅ {out}  ({os.path.getsize(out) // 1024} KB)")
print("   ⚠ Layout mirrored to RTL — replace placeholder text with real Arabic via Noto Naskh Arabic.")
