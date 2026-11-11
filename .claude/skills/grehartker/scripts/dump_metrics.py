import fontforge, json, csv, sys
from commun import fore_bbox

src, outdir = sys.argv[1], sys.argv[2]
f = fontforge.open(src)

params = {}
for k in ["fontname", "familyname", "fullname", "weight", "version", "em", "ascent", "descent",
          "italicangle", "upos", "uwidth", "os2_version", "os2_typoascent", "os2_typodescent",
          "os2_typolinegap", "os2_winascent", "os2_windescent", "hhea_ascent", "hhea_descent",
          "hhea_linegap", "os2_use_typo_metrics", "os2_vendor", "os2_weight", "os2_width",
          "os2_fstype", "os2_panose", "os2_strikeypos", "os2_strikeysize",
          "os2_subxsize", "os2_subysize", "os2_subyoff", "os2_supxsize", "os2_supysize", "os2_supyoff"]:
    try:
        v = getattr(f, k)
        params[k] = list(v) if isinstance(v, tuple) else v
    except Exception as e:
        params[k] = "ERR " + str(e)
params["layers"] = [f.layers[i].name for i in range(f.layer_cnt)]
params["gsub_lookups"] = list(f.gsub_lookups)
params["gpos_lookups"] = list(f.gpos_lookups)
params["glyph_count"] = len(list(f.glyphs()))
params["private"] = {k: f.private[k] for k in f.private} if f.private else {}

def decode(n):
    return n.replace("B", ">").replace("N", "-").replace("E", "!").replace("T", "~")

rows = []
for g in f.glyphs():
    xmin, ymin, xmax, ymax = fore_bbox(g)
    fg = g.layers["Fore"]
    rows.append({
        "glyphname": g.glyphname,
        "nabc": decode(g.glyphname),
        "unicode": ("U+%04X" % g.unicode) if g.unicode >= 0 else "",
        "encoding": g.encoding,
        "in_nabc_range": 0xE400 <= g.encoding < 0xF000,
        "width": g.width,
        "xmin": round(xmin, 1), "ymin": round(ymin, 1), "xmax": round(xmax, 1), "ymax": round(ymax, 1),
        "lsb": round(g.left_side_bearing, 1), "rsb": round(g.right_side_bearing, 1),
        "contours": len(fg),
        "references": ";".join(r[0] for r in g.references),
        "back_image": False,
        "comment": (g.comment or "").replace("\n", " "),
    })

# background images are not exposed in the python API: read them from the sfd text
img = {}
cur = None
with open(src, encoding="latin-1") as fh:
    for line in fh:
        if line.startswith("StartChar: "):
            cur = line.split(": ", 1)[1].strip()
        elif line.startswith("Image2: ") or line.startswith("Image: "):
            parts = line.split()
            img.setdefault(cur, []).append(parts[1:])
for r in rows:
    if r["glyphname"] in img:
        r["back_image"] = True
        r["image_info"] = " | ".join(" ".join(p) for p in img[r["glyphname"]])
    else:
        r["image_info"] = ""

with open(outdir + "/" + f.fontname + "_params.json", "w", encoding="utf-8") as fh:
    json.dump(params, fh, indent=1, ensure_ascii=False)
with open(outdir + "/" + f.fontname + "_glyphs.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "glyphs")
