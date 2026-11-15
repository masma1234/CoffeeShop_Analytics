"""Sampled process-tree resources and optional device-wide NVIDIA telemetry."""
from __future__ import annotations
import shutil
import subprocess
import threading
import time
import psutil


class ResourceMonitor:
    def __init__(self):
        self.root=psutil.Process();self.stop_event=threading.Event();self.started=time.perf_counter()
        self.cpu={};self.gpu_samples=0;self.gpu_peak_util=None;self.gpu_peak_memory=None;self.peak_rss=0;self.thread=None
        self.smi=shutil.which("nvidia-smi")

    def sample(self):
        memory=0
        try:processes=[self.root,*self.root.children(recursive=True)]
        except psutil.Error:return
        for process in processes:
            try:
                identity=(process.pid,process.create_time());cpu=process.cpu_times()
                self.cpu[identity]=max(self.cpu.get(identity,0),cpu.user+cpu.system)
                memory+=process.memory_info().rss
            except psutil.Error:continue
        self.peak_rss=max(self.peak_rss,memory)

    def run(self):
        while not self.stop_event.is_set():
            self.sample()
            if self.smi:
                try:
                    r=subprocess.run([self.smi,"--query-gpu=index,utilization.gpu,memory.used","--format=csv,noheader,nounits"],
                        capture_output=True,text=True,timeout=2,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                    if r.returncode==0:
                        for line in r.stdout.splitlines():
                            index,util_text,memory_text=[x.strip() for x in line.split(",")]
                            int(index);util=float(util_text);memory=float(memory_text)
                            self.gpu_samples+=1
                            self.gpu_peak_util=max(self.gpu_peak_util or 0,util)
                            self.gpu_peak_memory=max(self.gpu_peak_memory or 0,memory)
                except (OSError,ValueError,subprocess.TimeoutExpired):pass
            self.stop_event.wait(.5)

    def start(self):
        self.sample();self.initial_cpu=sum(self.cpu.values())
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()

    def stop(self):
        self.sample();self.stop_event.set()
        if self.thread:self.thread.join(timeout=3)
        elapsed=max(.000001,time.perf_counter()-self.started)
        return {"sampled_process_tree_cpu_percent_one_core":100*max(0,sum(self.cpu.values())-self.initial_cpu)/elapsed,
            "sampled_process_tree_peak_rss_bytes":self.peak_rss,
            "gpu_device_samples":self.gpu_samples,
            "gpu_device_peak_utilization_percent":self.gpu_peak_util,
            "gpu_device_peak_memory_used_mib":self.gpu_peak_memory,
            "scope":"Sampled process tree; CPU can exceed 100%; RSS sums shared pages. NVIDIA utilization/memory are whole-device, not exclusive to this job; fast child exits may be undercounted."}
