"""Checks native inference dependencies, rather than trusting package metadata."""
from __future__ import annotations


def backend_health() -> dict:
    import torch
    import torchvision
    boxes = torch.tensor([[0., 0., 10., 10.], [0., 0., 10., 10.]])
    selected = torchvision.ops.nms(boxes, torch.tensor([.9, .8]), .5)
    if selected.tolist() != [0]:
        raise RuntimeError("TorchVision NMS operator self-check failed")
    return {"status": "ok", "torch": torch.__version__, "torchvision": torchvision.__version__,
            "cpu_nms": "passed", "cuda_available": torch.cuda.is_available(),
            "scope": "Native backend compatibility only; no model accuracy tested"}
