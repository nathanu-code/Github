"""Footage analysis: where is the important action in each part of the clip?

For sampled frames we build an importance map from:
  * object detections (people, vehicles, boats, animals) from YOLOX (OpenCV model zoo, Apache-2.0),
  * faces (YuNet),
  * local motion (frame difference with global/camera motion removed),
  * spectral-residual visual saliency.
The maps drive the reframing crop path and banner placement.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .. import config

MODEL_DIR = config.ROOT / "assets" / "models"
YOLOX = MODEL_DIR / "object_detection_yolox_2022nov.onnx"
YUNET = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
TEXTDET = MODEL_DIR / "text_detection_en_ppocrv3_2023may.onnx"

# COCO ids that count as "subjects" in disaster footage, with weights.
SUBJECT_CLASSES = {0: 1.0,                                 # person
                   1: 0.6, 2: 0.8, 3: 0.6, 5: 0.8, 7: 0.8,  # bicycle, car, motorcycle, bus, truck
                   4: 0.6, 6: 0.6, 8: 0.7,                  # airplane, train, boat
                   15: 0.5, 16: 0.5, 17: 0.5, 18: 0.5, 19: 0.5}  # animals

MAP_W = 96  # importance maps are stored at this width


@dataclass
class Probe:
    width: int
    height: int
    fps: float
    duration: float
    has_audio: bool
    rotation: int = 0
    sar: str = "1:1"

    @property
    def display_size(self) -> tuple[int, int]:
        if self.rotation in (90, 270, -90, -270):
            return self.height, self.width
        return self.width, self.height


def probe(path: str | Path) -> Probe:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True).stdout
    info = json.loads(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    if not 1 <= fps <= 120:
        fps = 30.0
    rotation = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rotation = int(sd["rotation"])
    rotation = int(v.get("tags", {}).get("rotate", rotation))
    duration = float(info["format"].get("duration") or v.get("duration") or 0)
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    return Probe(int(v["width"]), int(v["height"]), fps, duration, has_audio, rotation,
                 v.get("sample_aspect_ratio", "1:1"))


@dataclass
class Analysis:
    times: np.ndarray                 # sample timestamps (s, relative to trim start)
    maps: np.ndarray                  # (n, mh, MAP_W) float32, each map sums to 1
    src_size: tuple[int, int]         # display width, height of the source
    detections: list[list[tuple]] = field(default_factory=list)  # per sample: (cls, score, x0,y0,x1,y1) normalised
    detector: str = "motion+saliency"
    text_maps: np.ndarray | None = None   # (n, mh, MAP_W) burned-in text coverage (0..1 per cell)
    text_boxes: list[list[tuple]] = field(default_factory=list)  # per sample: (x0,y0,x1,y1) normalised

    def burned_in_text(self) -> dict:
        """Share of samples with on-screen text, and boxes that persist (likely watermarks/logos)."""
        if self.text_maps is None:
            return {"share": 0.0, "persistent": []}
        has = [bool(b) for b in self.text_boxes]
        persistent = []
        if len(self.text_maps):
            freq = (self.text_maps > 0.3).mean(0)
            ys, xs = np.where(freq > 0.6)
            if len(xs):
                mh, mw = freq.shape
                persistent.append((round(xs.min() / mw, 2), round(ys.min() / mh, 2),
                                   round((xs.max() + 1) / mw, 2), round((ys.max() + 1) / mh, 2)))
        return {"share": round(float(np.mean(has)) if has else 0.0, 2), "persistent": persistent}

    def map_at(self, t: float) -> np.ndarray:
        i = int(np.clip(np.searchsorted(self.times, t), 0, len(self.times) - 1))
        return self.maps[i]


class _Detector:
    def __init__(self):
        self.net = None
        self.face = None
        if YOLOX.exists():
            self.net = cv2.dnn.readNetFromONNX(str(YOLOX))
            strides = [8, 16, 32]
            grids, exp = [], []
            for s in strides:
                g = 640 // s
                xv, yv = np.meshgrid(np.arange(g), np.arange(g))
                grids.append(np.stack((xv, yv), 2).reshape(1, -1, 2))
                exp.append(np.full((1, g * g, 1), s))
            self.grids = np.concatenate(grids, 1)
            self.strides = np.concatenate(exp, 1)
        if YUNET.exists():
            self.face = cv2.FaceDetectorYN.create(str(YUNET), "", (320, 320), 0.7, 0.3, 50)
        self.text = None
        if TEXTDET.exists():
            self.text = cv2.dnn_TextDetectionModel_DB(str(TEXTDET))
            self.text.setBinaryThreshold(0.3).setPolygonThreshold(0.5).setMaxCandidates(200).setUnclipRatio(2.0)
            self.text.setInputParams(1.0 / 255.0, (736, 736), (122.67891434, 116.66876762, 104.00698793), True)

    def texts(self, bgr: np.ndarray) -> list[tuple]:
        if self.text is None:
            return []
        h, w = bgr.shape[:2]
        boxes, _ = self.text.detect(cv2.resize(bgr, (736, 736)))
        out = []
        for b in boxes:
            a = np.array(b, float)
            x0, y0 = a.min(0) / 736
            x1, y1 = a.max(0) / 736
            if (x1 - x0) * (y1 - y0) > 0.0004:
                out.append((max(0, x0), max(0, y0), min(1, x1), min(1, y1)))
        return out

    @property
    def name(self) -> str:
        parts = (["yolox"] if self.net is not None else []) + (["yunet"] if self.face is not None else []) + \
                (["ppocr-text"] if self.text is not None else [])
        return "+".join(parts + ["motion", "saliency"])

    def objects(self, bgr: np.ndarray) -> list[tuple]:
        if self.net is None:
            return []
        h, w = bgr.shape[:2]
        r = min(640 / h, 640 / w)
        canvas = np.full((640, 640, 3), 114, np.uint8)
        canvas[: int(h * r), : int(w * r)] = cv2.resize(bgr, (int(w * r), int(h * r)))
        blob = cv2.dnn.blobFromImage(canvas)
        self.net.setInput(blob)
        out = self.net.forward()[0]
        out[:, :2] = (out[:, :2] + self.grids[0]) * self.strides[0]
        out[:, 2:4] = np.exp(out[:, 2:4]) * self.strides[0]
        scores = out[:, 4:5] * out[:, 5:]
        cls = scores.argmax(1)
        conf = scores[np.arange(len(cls)), cls]
        keep = conf > 0.35
        boxes = out[keep, :4]
        cls, conf = cls[keep], conf[keep]
        xyxy = np.stack([boxes[:, 0] - boxes[:, 2] / 2, boxes[:, 1] - boxes[:, 3] / 2,
                         boxes[:, 0] + boxes[:, 2] / 2, boxes[:, 1] + boxes[:, 3] / 2], 1) / r
        idx = cv2.dnn.NMSBoxes([[float(b[0]), float(b[1]), float(b[2] - b[0]), float(b[3] - b[1])] for b in xyxy],
                               conf.tolist(), 0.35, 0.45)
        res = []
        for i in np.array(idx).flatten():
            c = int(cls[i])
            if c in SUBJECT_CLASSES:
                x0, y0, x1, y1 = xyxy[i]
                res.append((c, float(conf[i]), max(0, x0 / w), max(0, y0 / h), min(1, x1 / w), min(1, y1 / h)))
        return res

    def faces(self, bgr: np.ndarray) -> list[tuple]:
        if self.face is None:
            return []
        h, w = bgr.shape[:2]
        self.face.setInputSize((w, h))
        _, faces = self.face.detect(bgr)
        if faces is None:
            return []
        return [(-1, float(f[-1]), f[0] / w, f[1] / h, (f[0] + f[2]) / w, (f[1] + f[3]) / h) for f in faces]


def _spectral_saliency(gray: np.ndarray) -> np.ndarray:
    small = cv2.resize(gray, (64, max(8, int(64 * gray.shape[0] / gray.shape[1])))).astype(np.float32)
    f = np.fft.fft2(small)
    log_amp = np.log(np.abs(f) + 1e-6)
    residual = log_amp - cv2.blur(log_amp, (3, 3))
    sal = np.abs(np.fft.ifft2(np.exp(residual + 1j * np.angle(f)))) ** 2
    sal = cv2.GaussianBlur(sal, (0, 0), 2.5)
    return cv2.resize(sal, (gray.shape[1], gray.shape[0]))


def _norm(m: np.ndarray) -> np.ndarray:
    s = float(m.sum())
    return m / s if s > 0 else np.full_like(m, 1.0 / m.size)


def analyze(path: str | Path, start: float = 0.0, end: float | None = None, sample_fps: float = 3.0,
            analysis_width: int = 640) -> Analysis:
    pr = probe(path)
    dw, dh = pr.display_size
    aw = analysis_width
    ah = int(round(dh * aw / dw / 2) * 2)
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    cmd += ["-i", str(path), "-vf", f"fps={sample_fps},scale={aw}:{ah}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    det = _Detector()
    mh = max(8, int(round(MAP_W * dh / dw)))
    maps, times, dets, tmaps, tboxes = [], [], [], [], []
    prev = None
    frame_bytes = aw * ah * 3
    k = 0
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        bgr = np.frombuffer(buf, np.uint8).reshape(ah, aw, 3)
        gray = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), (5, 5), 0)

        imp = np.zeros((ah, aw), np.float32)
        # local motion, with camera motion compensated by phase correlation
        if prev is not None:
            (dx, dy), _ = cv2.phaseCorrelate(prev.astype(np.float32), gray.astype(np.float32))
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            aligned = cv2.warpAffine(prev, M, (aw, ah), borderMode=cv2.BORDER_REPLICATE)
            diff = cv2.absdiff(gray, aligned).astype(np.float32)
            diff = np.maximum(0, diff - np.median(diff) - 6)
            imp += 0.35 * _norm(cv2.GaussianBlur(diff, (0, 0), 9))
        prev = gray
        imp += 0.25 * _norm(_spectral_saliency(gray))
        tb = det.texts(bgr)
        if tb:   # burned-in captions are salient but are not the action: damp them
            tmask = np.zeros_like(imp)
            for x0, y0, x1, y1 in tb:
                tmask[int(y0 * ah):int(np.ceil(y1 * ah)), int(x0 * aw):int(np.ceil(x1 * aw))] = 1.0
            imp *= 1.0 - 0.85 * tmask

        boxes = det.objects(bgr) + det.faces(bgr)
        if boxes:
            box_map = np.zeros_like(imp)
            for c, sc, x0, y0, x1, y1 in boxes:
                wgt = (SUBJECT_CLASSES.get(c, 1.2)) * sc
                X0, Y0, X1, Y1 = int(x0 * aw), int(y0 * ah), int(np.ceil(x1 * aw)), int(np.ceil(y1 * ah))
                area = max(1, (X1 - X0) * (Y1 - Y0))
                # small, distant subjects still matter: weight by sqrt(area) not area
                box_map[Y0:Y1, X0:X1] += wgt * np.sqrt(area) / area
            imp += 0.55 * _norm(cv2.GaussianBlur(box_map, (0, 0), 3))
        dets.append(boxes)
        tboxes.append(tb)
        tm = np.zeros((mh, MAP_W), np.float32)
        for x0, y0, x1, y1 in tb:
            tm[int(y0 * mh):int(np.ceil(y1 * mh)), int(x0 * MAP_W):int(np.ceil(x1 * MAP_W))] = 1.0
        tmaps.append(tm)
        maps.append(_norm(cv2.resize(imp, (MAP_W, mh), interpolation=cv2.INTER_AREA)))
        times.append(k / sample_fps)
        k += 1
    proc.wait()
    if not maps:
        raise RuntimeError(f"could not decode frames from {path}")
    return Analysis(np.array(times), np.stack(maps).astype(np.float32), (dw, dh), dets, det.name,
                    np.stack(tmaps), tboxes)
