"""Local PTS decoding and MP4 encoding in bounded, deadline-controlled workers."""
from __future__ import annotations

from fractions import Fraction
import multiprocessing as mp
from pathlib import Path
import queue


ENCODER_TIME_BASE=Fraction(1,60000)


def source_position(frame,previous=None):
    if type(frame.pts) is not int or frame.time_base is None or frame.time_base<=0:
        raise ValueError("Missing or invalid presentation timestamp; no FPS-based fabrication")
    position=Fraction(frame.pts)*frame.time_base
    if previous is not None and position<=previous:raise ValueError("Video PTS must strictly increase")
    return position


def _put(output,item,stop):
    while not stop.is_set():
        try:output.put(item,timeout=.1);return
        except queue.Full:continue


def _decode_pts(source,output,stop):
    try:
        import av
        with av.open(source,timeout=15) as container:
            if not container.streams.video:raise ValueError("Input contains no video stream")
            stream=container.streams.video[0]
            _put(output,("metadata",{"width":stream.width,"height":stream.height,
                "rate":str(stream.average_rate or Fraction(25)),"time_base":str(stream.time_base),
                "declared_frames":stream.frames,"declared_duration_seconds":float(stream.duration*stream.time_base) if stream.duration is not None else None}),stop)
            previous,first,count=None,None,0
            for index,frame in enumerate(container.decode(stream)):
                if stop.is_set():return
                position=source_position(frame,previous)
                if first is None:first=position
                previous=position;count+=1
                _put(output,("frame",(index,frame.pts,str(frame.time_base),position-first,frame.to_ndarray(format="bgr24"))),stop)
            if stream.frames>0 and count<stream.frames:raise OSError("Truncated video: decoded fewer frames than declared")
            _put(output,("eof",count),stop)
    except Exception as exc:_put(output,("error",f"{type(exc).__name__}: {exc}"),stop)


def _encode_pts(destination,width,height,rate,inputs,status,stop):
    try:
        import av
        import numpy as np
        with av.open(destination,mode="w",format="mp4") as container:
            stream=container.add_stream("mpeg4",rate=Fraction(rate))
            stream.width=width+width%2;stream.height=height+height%2
            stream.pix_fmt="yuv420p";stream.bit_rate=2_000_000
            stream.time_base=ENCODER_TIME_BASE;stream.codec_context.time_base=ENCODER_TIME_BASE
            stream.codec_context.max_b_frames=0
            while not stop.is_set():
                try:item=inputs.get(timeout=.1)
                except queue.Empty:continue
                if item is None:break
                image,pts=item
                if image.shape[:2]!=(height,width):raise ValueError("Frame dimensions changed during encoding")
                if width%2 or height%2:image=np.pad(image,((0,height%2),(0,width%2),(0,0)))
                frame=av.VideoFrame.from_ndarray(image,format="bgr24")
                frame.pts=pts;frame.time_base=ENCODER_TIME_BASE
                for packet in stream.encode(frame):container.mux(packet)
            for packet in stream.encode():container.mux(packet)
        status.put(("ok",None))
    except Exception as exc:status.put(("error",f"{type(exc).__name__}: {exc}"))


def _close_process(process,queues,stop):
    stop.set();process.join(timeout=1)
    if process.is_alive():process.terminate();process.join(timeout=2)
    for q in queues:q.close();q.cancel_join_thread()


class PTSVideoInput:
    def __init__(self,source,timeout=15):
        if not Path(source).is_file():raise FileNotFoundError(source)
        ctx=mp.get_context("spawn");self.queue=ctx.Queue(maxsize=2);self.stop=ctx.Event()
        self.timeout=timeout;self.metadata={};self.closed=False
        self.process=ctx.Process(target=_decode_pts,args=(str(source),self.queue,self.stop),daemon=True)
        self.process.start()

    def __iter__(self):
        while True:
            try:kind,data=self.queue.get(timeout=self.timeout)
            except queue.Empty as exc:raise TimeoutError("PTS decoder read deadline exceeded") from exc
            if kind=="error":raise OSError(data)
            if kind=="metadata":self.metadata=data
            elif kind=="frame":yield data
            elif kind=="eof":
                if not data:raise ValueError("Input contains no decoded frames")
                return

    def close(self):
        if not self.closed:
            _close_process(self.process,[self.queue],self.stop);self.closed=True


class PTSVideoWriter:
    def __init__(self,destination,width,height,rate,timeout=30):
        if Path(destination).exists():raise FileExistsError(destination)
        ctx=mp.get_context("spawn");self.queue=ctx.Queue(maxsize=2);self.status=ctx.Queue(maxsize=1);self.stop=ctx.Event()
        self.timeout=timeout;self.closed=False;self.previous=-1;self.max_rounding_error=0.
        self.process=ctx.Process(target=_encode_pts,args=(str(destination),width,height,rate,self.queue,self.status,self.stop),daemon=True)
        self.process.start()

    def write(self,image,seconds):
        pts=round(Fraction(seconds)/ENCODER_TIME_BASE)
        if pts<=self.previous:raise ValueError("Output timestamp precision cannot represent this frame ordering")
        self.previous=pts
        self.max_rounding_error=max(self.max_rounding_error,float(abs(Fraction(seconds)-pts*ENCODER_TIME_BASE)))
        self._put((image,pts))

    def _put(self,item):
        if not self.process.is_alive():
            self._result(.2)
            raise RuntimeError("Encoder exited before completing the video")
        try:self.queue.put(item,timeout=self.timeout)
        except queue.Full as exc:raise TimeoutError("MP4 encoder input deadline exceeded") from exc

    def _result(self,timeout):
        try:kind,data=self.status.get(timeout=timeout)
        except queue.Empty as exc:raise TimeoutError("MP4 encoder completion deadline exceeded") from exc
        if kind=="error":raise RuntimeError(data)

    def close(self,abort=False):
        if self.closed:return
        try:
            if not abort:
                self._put(None);self._result(self.timeout)
        finally:
            _close_process(self.process,[self.queue,self.status],self.stop);self.closed=True
