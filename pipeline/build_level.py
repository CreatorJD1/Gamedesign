#!/usr/bin/env python3
"""
build_level.py - reference pipeline for Soul Drift's per-level system.

Takes a level's three layer images and:
  - keys white -> alpha (uploaded art stores "transparent" as flat white),
  - derives one-way platform collision from the midground island CROWNS,
  - encodes bg/mid/fg to WebP base64,
  - prints a LEVELS[idx] entry you can paste into the HTML (or wire it into your build step),
  - writes a collision-overlay PNG so you can eyeball the floors vs the art BEFORE committing.

Usage:
  python3 build_level.py --bg bg.png --mid mid.png --fg fg.png --out level_data.json
Requires: pillow, numpy, scipy   (pip install pillow numpy scipy)

NOTE: collision is placed on the dense cloud crown (first row reaching ~50% of the
island's max width), NOT the wispy top, or the character floats. Platforms are made
one-way at runtime (checkCollision.down/left/right = false) so she can't snag sides.
"""
import argparse, io, base64, json
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage

CROWN_WIDTH_FRAC = 0.50   # crown = first row with width >= this * island_max_width
PLAT_WIDTH_FRAC  = 0.70   # collision bar width as fraction of island width
MIN_ISLAND_FRAC  = 0.0012 # ignore components smaller than this fraction of the image
MIN_ISLAND_W_PX  = 60     # ignore islands narrower than this (source px)
COLL_THICK_PX    = 18     # nominal collision thickness in source px (runtime enforces >=28 world px)

def graded_alpha(im):
    a = np.asarray(im.convert('RGB')).astype(np.float32)
    r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    al = np.clip((sat - 0.05) * 3.2, 0, 1) * 255
    mist = np.clip((250 - mn) / 60, 0, 1) * 90
    al = np.maximum(al, mist)
    al = np.where((mn > 248) & (sat < 0.05), 0, al).astype(np.uint8)
    return Image.fromarray(al, 'L').filter(ImageFilter.GaussianBlur(0.7))

def derive_crown_rects(mid_rgba):
    W, H = mid_rgba.size
    alpha = np.asarray(mid_rgba)[:,:,3]
    solid = (alpha > 150).astype(np.uint8)
    solid = ndimage.binary_closing(solid, iterations=2).astype(np.uint8)
    solid = ndimage.binary_opening(solid, iterations=1).astype(np.uint8)
    lab, n = ndimage.label(solid)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    rects = []
    for i in range(n):
        if sizes[i] < H * W * MIN_ISLAND_FRAC:
            continue
        cid = i + 1
        ys, xs = np.where(lab == cid)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        Wisl = x1 - x0 + 1
        if Wisl < MIN_ISLAND_W_PX:
            continue
        roww = np.array([(lab[yy, x0:x1+1] == cid).sum() for yy in range(y0, y1+1)])
        Wmax = roww.max()
        cr = np.where(roww >= CROWN_WIDTH_FRAC * Wmax)[0]
        if len(cr) == 0:
            continue
        crown_top = y0 + int(cr[0])
        cw = Wisl * PLAT_WIDTH_FRAC
        cx = (x0 + x1) / 2
        rects.append([round((cx - cw/2)/W, 4), round(crown_top/H, 4),
                      round(cw/W, 4), round(COLL_THICK_PX/H, 4)])
    return rects

def enc_webp(im, q=86):
    buf = io.BytesIO(); im.save(buf, 'WEBP', quality=q, method=4)
    return base64.b64encode(buf.getvalue()).decode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bg', required=True); ap.add_argument('--mid', required=True)
    ap.add_argument('--fg', required=True); ap.add_argument('--idx', type=int, default=0)
    ap.add_argument('--maxw', type=int, default=1500)
    ap.add_argument('--out', default='level_data.json')
    args = ap.parse_args()

    def load_scaled(p, w):
        im = Image.open(p).convert('RGB')
        return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)

    bg = load_scaled(args.bg, args.maxw)
    mid_rgb = load_scaled(args.mid, args.maxw)
    fg = load_scaled(args.fg, args.maxw)

    mid = mid_rgb.convert('RGBA'); mid.putalpha(graded_alpha(mid_rgb))
    fgr = fg.convert('RGBA'); fgr.putalpha(graded_alpha(fg))

    rects = derive_crown_rects(mid)
    print(f"derived {len(rects)} crown-aligned platforms")

    keys = {f"L{args.idx+1}_bg": enc_webp(bg, 84),
            f"L{args.idx+1}_mid": enc_webp(mid, 86),
            f"L{args.idx+1}_fg": enc_webp(fgr, 84)}
    json.dump({"idx": args.idx, "assets_b64": keys, "rects": rects}, open(args.out, 'w'))

    # overlay preview
    W, H = mid.size
    prev = Image.new('RGBA', (W, H), (20, 18, 34, 255)); prev.alpha_composite(mid)
    d = ImageDraw.Draw(prev)
    for nx, ny, nw, nh in rects:
        x, y, w2 = nx*W, ny*H, nw*W
        d.line([(x, y), (x + w2, y)], fill=(255, 40, 80), width=6)
    prev.convert('RGB').save(args.out.replace('.json', '_overlay.png'))

    print(f"wrote {args.out} and overlay PNG")
    print(f"\nPaste into LEVELS[{args.idx}] (and add the 3 keys to ASSETS):")
    print(f"  {{art:1, bg:'L{args.idx+1}_bg', mid:'L{args.idx+1}_mid', fg:'L{args.idx+1}_fg', rects:{json.dumps(rects)}}}")

if __name__ == '__main__':
    main()
