import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = "/tmp/claude-0/-home-user-RamaBK/a8f551f7-734b-53c1-83ca-c899237d20fb/scratchpad"
STILLS = f"{ROOT}/stills"
OUT = f"{ROOT}/vid_free"
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FPS = 25

RED, BLUE, YELLOW = "0xFF4B4B", "0x4DA3FF", "0xFFD400"

# (name, EN, FR, ES, duration, t_en, t_fr, t_es)
SCENES = [
    ("intro",      "Hello!",      "Bonjour !",   "¡Hola!",         6, 1.5, 2.6, 3.7),
    ("apple",      "apple",       "la pomme",    "la manzana",     8, 2.6, 4.3, 6.0),
    ("banana",     "banana",      "la banane",   "el plátano",     8, 2.6, 4.3, 6.0),
    ("strawberry", "strawberry",  "la fraise",   "la fresa",       8, 2.6, 4.3, 6.0),
    ("orange",     "orange",      "l'orange",    "la naranja",     8, 2.6, 4.3, 6.0),
    ("grapes",     "grapes",      "le raisin",   "las uvas",       8, 2.6, 4.3, 6.0),
    ("pear",       "pear",        "la poire",    "la pera",        8, 2.6, 4.3, 6.0),
    ("watermelon", "watermelon",  "la pastèque", "la sandía",      8, 2.6, 4.3, 6.0),
    ("lemon",      "lemon",       "le citron",   "el limón",       8, 2.6, 4.3, 6.0),
    ("cherry",     "cherry",      "la cerise",   "la cereza",      8, 2.6, 4.3, 6.0),
    ("pineapple",  "pineapple",   "l'ananas",    "la piña",        8, 2.6, 4.3, 6.0),
    ("finale",     "Bye!",        "À bientôt !", "¡Hasta pronto!", 6, 1.5, 2.6, 3.7),
]

def motion(i, n):
    # i-th camera move, n frames. Input is 3840x2160.
    k = i % 5
    if k == 0:   # slow zoom in, centre
        return f"z='1+0.13*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if k == 1:   # pan left to right
        return f"z='1.12':x='(iw-iw/zoom)*on/{n}':y='(ih-ih/zoom)/2'"
    if k == 2:   # zoom out
        return f"z='1.13-0.13*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if k == 3:   # pan right to left
        return f"z='1.12':x='(iw-iw/zoom)*(1-on/{n})':y='(ih-ih/zoom)/2'"
    return f"z='1+0.13*on/{n}':x='(iw-iw/zoom)*0.8':y='(ih-ih/zoom)*0.7'"  # zoom in toward lower right

def build(idx):
    name, en, fr, es, D, t1, t2, t3 = SCENES[idx]
    n = D * FPS
    src = f"{STILLS}/s{idx+1:02d}.png"
    dst = f"{OUT}/c{idx+1:02d}_{name}.mp4"
    # text files (avoid escaping problems)
    tf = []
    for j, txt in enumerate((en, fr, es)):
        p = f"{OUT}/t{idx+1:02d}_{j}.txt"
        open(p, "w", encoding="utf-8").write(txt)
        tf.append(p)
    ys = (790, 880, 970)
    cols = (RED, BLUE, YELLOW)
    ts = (t1, t2, t3)
    dt = []
    for p, y, c, t in zip(tf, ys, cols, ts):
        dt.append(
            f"drawtext=fontfile={FONT}:textfile={p}:fontsize=72:fontcolor={c}:"
            f"borderw=5:bordercolor=white:box=1:boxcolor=black@0.45:boxborderw=14:"
            f"x=(w-text_w)/2:y={y}:enable='gte(t,{t})'"
        )
    vf = (f"scale=3840:2160:flags=lanczos,zoompan={motion(idx,n)}:d={n}:s=1920x1080:fps={FPS},"
          + ",".join(dt) +
          f",fade=t=in:st=0:d=0.3,fade=t=out:st={D-0.3}:d=0.3,format=yuv420p")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-t", str(D),
           "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", str(FPS), dst]
    subprocess.run(cmd, check=True)
    return dst

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as ex:
        clips = list(ex.map(build, range(len(SCENES))))
    lst = f"{OUT}/list.txt"
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    final = f"{OUT}/video1_fruits_free_16x9.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", final], check=True)
    # SRT + timing sheet
    def ts(x):
        h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}"
    srt, csv, t0, k = [], ["scene,start_s,end_s,en_at_s,fr_at_s,es_at_s,EN,FR,ES"], 0.0, 1
    for name, en, fr, es, D, t1, t2, t3 in SCENES:
        end = t0 + D - 0.2
        for txt, col, t in ((en, "#FF4B4B", t1), (fr, "#4DA3FF", t2), (es, "#FFD400", t3)):
            srt.append(f"{k}\n{ts(t0+t)} --> {ts(end)}\n<font color=\"{col}\">{txt}</font>\n")
            k += 1
        csv.append(f"{name},{t0:.1f},{t0+D:.1f},{t0+t1:.1f},{t0+t2:.1f},{t0+t3:.1f},{en},{fr},{es}")
        t0 += D
    open(f"{OUT}/video1_fruits_subtitles.srt", "w", encoding="utf-8").write("\n".join(srt))
    open(f"{OUT}/video1_voice_timing.csv", "w", encoding="utf-8").write("\n".join(csv) + "\n")
    print("done", final, "total", t0, "s")
