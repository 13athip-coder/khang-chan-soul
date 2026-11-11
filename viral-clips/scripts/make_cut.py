#!/usr/bin/env python3
"""Build the 15s viral property cut. Config-driven: edit SEGMENTS, re-run."""
import os, subprocess, sys

U   = "/root/.claude/uploads/40b33566-4cec-5512-87f1-e49c0bc23514"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/out"
W, H, FPS = 1080, 1920, 30
WHIP = 0.40   # seconds of source eaten by each whip
WSPD = 4.0    # whip speed multiplier

C = {
 1:"06fba50d-video_640140969513058323-qf8UDv7d.mp4",
 2:"1ac4c960-_ExQkWsO00EVRglQrFS9QSY5EJRSyZuD3TN-iXbHG_Y.mp4",
 3:"321f85af-video_640140825732579781-iVh6aW3I.mp4",
 4:"41b7a243-video_640141335357817057-UrtiIbRv.mp4",
 5:"533cb9dc-video_640141329317233070-uHywzQdG.mp4",
 6:"86ff04bf-video_640141335172481866-hsYFUcHd.mp4",
 7:"882fce53-LaKPwvZiQ8xmrFrUR7NgtgrWUbCNAd48MdiiX223pds.mp4",
 8:"db654421-0Ll3kOmIXBz7in4TkjLByt0DYRokJehYO9CHR_6OHcg.mp4",
 9:"dbc6244f-video_640141330911854900-AkGz9nPj.mp4",
10:"fc62de6e-9cpIjyz2mexZgkp5GCpiajd55EVfJJ0PYsjmE78OrtI.mp4",
}
SCALE = f"scale={W}:{H}:flags=lanczos,setsar=1"
SHARP = "unsharp=5:5:0.45:5:5:0.0"

# (tag, clip, src_in, src_out, whip_in, whip_out)  -> 1.2s slot each
SEGMENTS = [
 ("01_hook_living",  9, 0.70, 2.50, False, True ),
 ("02_living_cab",   1, 0.60, 2.40, True,  True ),
 ("03_living_door", 10, 0.90, 2.70, True,  True ),
 ("04_kitchen_a",    8, 0.50, 2.30, True,  True ),
 ("05_kitchen_win",  5, 6.60, 8.40, True,  True ),
 ("06_bedB_curtain", 7, 0.30, 2.10, True,  True ),
 ("07_bedB_window",  6, 1.90, 3.70, True,  True ),
 ("08_bedA_wardrobe",2, 1.50, 3.30, True,  True ),
]
TWIST = dict(tag="09_twist_led", clip=3, win=0.60, fast_a=1.00, fast_b=3.60,
             slow_b=5.50, fast_spd=1.70, slot=4.80)
LOOP  = dict(tag="10_loop", clip=9, a=0.10, b=0.70)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); sys.exit(1)

def enc(fc, out):
    run(["ffmpeg","-v","error","-i",SRC,"-filter_complex",fc,"-map","[v]",
         "-r",str(FPS),"-an","-c:v","libx264","-preset","slow","-crf","14",
         "-pix_fmt","yuv420p",out,"-y"])

os.makedirs(OUT, exist_ok=True)
parts = []

for tag, clip, a, b, wi, wo in SEGMENTS:
    SRC = os.path.join(U, C[clip]); dst = os.path.join(OUT, tag + ".mp4")
    ba = a + (WHIP if wi else 0.0); bb = b - (WHIP if wo else 0.0)
    ch, lb = [], []
    if wi:
        ch.append(f"[0:v]trim={a}:{ba},setpts=(PTS-STARTPTS)/{WSPD},{SCALE},"
                  f"tmix=frames=5:weights='1 1 1 1 1'[wi]"); lb.append("[wi]")
    ch.append(f"[0:v]trim={ba}:{bb},setpts=PTS-STARTPTS,{SCALE},{SHARP}[bd]"); lb.append("[bd]")
    if wo:
        ch.append(f"[0:v]trim={bb}:{b},setpts=(PTS-STARTPTS)/{WSPD},{SCALE},"
                  f"tmix=frames=5:weights='1 1 1 1 1'[wo]"); lb.append("[wo]")
    ch.append("".join(lb) + f"concat=n={len(lb)}:v=1[v]")
    enc(";".join(ch), dst); parts.append(dst)
    print(f"  {tag}  src {a}->{b}  out {(bb-ba)+ (WHIP/WSPD)*(wi+wo):.2f}s")

# --- twist: whip-in, fast approach, slow reveal on the LED headboard
t = TWIST; SRC = os.path.join(U, C[t["clip"]]); dst = os.path.join(OUT, t["tag"]+".mp4")
d_whip = WHIP / WSPD
d_fast = (t["fast_b"] - t["fast_a"]) / t["fast_spd"]
d_slow = t["slot"] - d_whip - d_fast
slow_mult = d_slow / (t["slow_b"] - t["fast_b"])
fc = (f"[0:v]trim={t['win']}:{t['fast_a']},setpts=(PTS-STARTPTS)/{WSPD},{SCALE},"
      f"tmix=frames=5:weights='1 1 1 1 1'[wi];"
      f"[0:v]trim={t['fast_a']}:{t['fast_b']},setpts=(PTS-STARTPTS)/{t['fast_spd']},{SCALE},{SHARP}[ft];"
      f"[0:v]trim={t['fast_b']}:{t['slow_b']},setpts={slow_mult:.4f}*(PTS-STARTPTS),{SCALE},{SHARP}[sl];"
      f"[wi][ft][sl]concat=n=3:v=1[v]")
enc(fc, dst); parts.append(dst)
print(f"  {t['tag']}  fast {t['fast_spd']}x -> slow {1/slow_mult:.2f}x  out {t['slot']:.2f}s")

# --- loop tail: ends on the exact frame the video opens with
l = LOOP; SRC = os.path.join(U, C[l["clip"]]); dst = os.path.join(OUT, l["tag"]+".mp4")
enc(f"[0:v]trim={l['a']}:{l['b']},setpts=PTS-STARTPTS,{SCALE},{SHARP}[v]", dst)
parts.append(dst); print(f"  {l['tag']}  out {l['b']-l['a']:.2f}s")

lst = os.path.join(OUT, "concat.txt")
open(lst,"w").write("".join(f"file '{p}'\n" for p in parts))
final = os.path.join(OUT, "base_cut.mp4")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",lst,
     "-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p",
     "-movflags","+faststart","-r",str(FPS),final,"-y"])
print("FINAL:", final)
