"""Actual local pretrained RT-DETR smoke on a public-photo loop, not café accuracy."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True)
    parser.add_argument("--device",default="cpu")
    parser.add_argument("--model-dir")
    args=parser.parse_args();output=Path(args.output).resolve()
    if output.exists():raise FileExistsError(output)
    photo=ROOT/"var/model-benchmark/coco8/images/val/000000000049.jpg"
    if not photo.is_file():raise FileNotFoundError("Existing public COCO8 fixture required; no automatic download")
    import av
    import numpy as np
    from PIL import Image
    from coffee_ops.schema import file_hash
    output.mkdir(parents=True,exist_ok=False)
    with Image.open(photo) as im:image=np.array(im.convert("RGB").resize((640,480)))
    source=output/"public-photo-loop.mp4"
    with av.open(str(source),mode="w") as container:
        stream=container.add_stream("mpeg4",rate=10);stream.width=640;stream.height=480;stream.pix_fmt="yuv420p"
        stream.time_base=Fraction(1,10000);stream.codec_context.time_base=Fraction(1,10000);stream.codec_context.max_b_frames=0
        for i in range(8):
            frame=av.VideoFrame.from_ndarray(image,format="rgb24");frame.pts=i*1000;frame.time_base=Fraction(1,10000)
            for packet in stream.encode(frame):container.mux(packet)
        for packet in stream.encode():container.mux(packet)
    commands=[]
    def run(arguments):
        result=subprocess.run([sys.executable,"-B","-m","coffee_ops",*arguments],cwd=ROOT,
            capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=180)
        commands.append({"command":[a.replace(str(output),"<output>") for a in arguments],"exit_code":result.returncode})
        if result.returncode:raise RuntimeError(result.stderr+result.stdout)
        return json.loads(result.stdout)
    prep=["prepare-video","--source",str(source),"--directory",str(output/"configuration"),"--device",args.device]
    if args.model_dir:prep += ["--model-dir",args.model_dir]
    prepared=run(prep)
    summary=run(["--config",prepared["config"],"annotate-video","--source",str(source),"--directory",str(output/"review"),
        "--camera","video","--run-id","public-photo-loop","--start","2026-01-01T09:00:00Z","--sample-every","1"])
    raw=json.loads((output/"review/detections.json").read_text(encoding="utf-8"))
    count=sum(len(f["detections"]) for f in raw["frames"])
    with av.open(str(output/"review/annotated.mp4")) as container:
        decoded=list(container.decode(video=0))
        pts=[float(f.pts*f.time_base) for f in decoded]
        decoded[min(3,len(decoded)-1)].to_image().save(output/"overlay-preview.jpg")
    if len(decoded)!=8 or any(abs(actual-i*.1)>1/60000 for i,actual in enumerate(pts)):
        raise AssertionError("Annotated output changed source PTS/frame count")
    if count==0:raise AssertionError("Actual pretrained detector returned no enabled-class proposals on fixture")
    tracked=json.loads((output/"review/predictions.json").read_text(encoding="utf-8"))
    if not any(f["detections"] for f in tracked["frames"]):raise AssertionError("Pretrained detections never reached tracking")
    if summary["prepared_drinks"] is not None or summary["confirmed_handovers"] is not None:
        raise AssertionError("Unsupported business action was reported as a measured count")
    evidence={"purpose":"actual_pretrained_inference_and_encoding_software_check_not_real_video_accuracy",
        "source":"Eight repeated frames of one existing public COCO8 photograph, resized to 640x480",
        "source_photo_sha256":file_hash(str(photo)),"source_video_sha256":file_hash(str(source)),
        "model":prepared["model"],"commands":commands,"summary":summary,
        "raw_proposal_rows":count,"output_frame_pts_seconds":pts,"frame_count_and_pts_passed":True,
        "accuracy_claims":False,"cafe_footage_available":False}
    (output/"verification.json").write_text(json.dumps(evidence,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"verified":True,"evidence":str(output/"verification.json"),"annotated_video":str(output/"review/annotated.mp4"),
        "raw_proposal_rows":count,"accuracy_claims":False}))


if __name__=="__main__":main()
