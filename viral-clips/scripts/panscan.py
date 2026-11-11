import subprocess, sys, numpy as np
W,H=160,284
def frames(path):
    cmd=["ffmpeg","-v","error","-i",path,"-vf",f"scale={W}:{H},format=gray","-f","rawvideo","-pix_fmt","gray","-"]
    raw=subprocess.run(cmd,capture_output=True).stdout
    n=len(raw)//(W*H)
    return np.frombuffer(raw[:n*W*H],dtype=np.uint8).reshape(n,H,W).astype(np.float32)
def shift1d(a,b,maxs=24):
    # best dx so that b(x) ~ a(x-dx)
    best=(1e18,0)
    for dx in range(-maxs,maxs+1):
        if dx>=0: d=a[:W-dx]-b[dx:]
        else: d=a[-dx:]-b[:W+dx]
        if len(d)<40: continue
        e=float(np.mean(d*d))
        if e<best[0]: best=(e,dx)
    return best[1]
path=sys.argv[1]; label=sys.argv[2]
f=frames(path)
prof=f.mean(axis=1)  # column profile per frame
dxs=[shift1d(prof[i],prof[i+1]) for i in range(len(f)-1)]
fps=30.0
dxs=np.array(dxs,dtype=float)
# px/frame in 160-wide space -> convert to 540-wide
dxs540=dxs*540/W
print(f"{label} nframes={len(f)} meandx={dxs540.mean():+.1f}px/f  start(first8)={dxs540[:8].round(0)} end(last8)={dxs540[-8:].round(0)}")
print("   perframe:", " ".join(f"{v:+.0f}" for v in dxs540))
