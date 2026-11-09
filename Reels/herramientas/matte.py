"""Person matte (alpha 0-1) for talking-head frames using MODNet (onnxruntime)."""
import os, numpy as np, onnxruntime as ort
from PIL import Image

MODEL = os.environ.get("REELS_MODNET", os.path.expanduser("~/.cache/reels-models/modnet.onnx"))
MODEL_URL = "https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx"

class Matter:
    def __init__(self, in_w=576, in_h=1024):
        if not os.path.exists(MODEL):
            os.makedirs(os.path.dirname(MODEL), exist_ok=True)
            import urllib.request; urllib.request.urlretrieve(MODEL_URL, MODEL)
        so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 4
        self.s = ort.InferenceSession(MODEL, so, providers=["CPUExecutionProvider"])
        self.w, self.h = in_w, in_h

    def __call__(self, rgb):  # rgb: HxWx3 uint8 -> HxW float32 alpha
        H, W = rgb.shape[:2]
        x = np.asarray(Image.fromarray(rgb).resize((self.w, self.h), Image.BILINEAR), np.float32)
        x = (x / 255.0 - 0.5) / 0.5
        a = self.s.run(None, {"input": x.transpose(2, 0, 1)[None]})[0][0, 0]
        a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255.0
        return a
