import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from skimage.feature import local_binary_pattern
import numpy as np

from config import CLASS_NAMES

IMG_SIZE = 224
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

img_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


class CornLeafNet(nn.Module):
    def __init__(self, num_classes=4, use_lbp=True, lbp_in_dim=59):
        super().__init__()

        base = models.mobilenet_v2(weights=None)

        self.use_lbp = use_lbp
        self.feature_extractor = base.features
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

        if use_lbp:
            in_feat = 1280 + lbp_in_dim   # 1280 + 59 = 1339
        else:
            in_feat = 1280

        self.fusion_normalization = nn.LayerNorm(in_feat)

        self.classifier = nn.Sequential(
            nn.Linear(in_feat, 220),
            nn.ReLU(inplace=True),

            nn.Linear(220, 120),
            nn.ReLU(inplace=True),

            nn.Linear(120, 60),
            nn.ReLU(inplace=True),

            nn.Dropout(0.2),

            nn.Linear(60, num_classes),
        )

    def forward(self, x, lbp_feat=None):
        x = self.feature_extractor(x)
        x = self.pool(x).flatten(1)

        if self.use_lbp and lbp_feat is not None:
            z = torch.cat([x, lbp_feat], dim=1)
        else:
            z = x

        z = self.fusion_normalization(z)
        return self.classifier(z)


def extract_lbp_features(pil_img, mode, out_dim):
    gray = pil_img.convert("L").resize((IMG_SIZE, IMG_SIZE))
    gray_np = np.array(gray, dtype=np.uint8)

    if mode == "classic":
        P, R, method, bins = 8, 1, "default", 256
    elif mode == "uniform":
        P, R, method, bins = 57, 1, "uniform", 59
    elif mode == "riu":
        P, R, method, bins = 8, 1, "uniform", 10
    else:
        return torch.zeros(out_dim)

    lbp = local_binary_pattern(gray_np, P=P, R=R, method=method)
    hist, _ = np.histogram(
        lbp.ravel(),
        bins=bins,
        range=(0, bins),
        density=True
    )

    feat = torch.tensor(hist, dtype=torch.float32)

    if feat.numel() < out_dim:
        feat = F.pad(feat, (0, out_dim - feat.numel()))

    return feat[:out_dim]


def load_model_from_path(model_path, use_lbp, lbp_in_dim):
    ckpt = torch.load(model_path, map_location="cpu")

    model = CornLeafNet(
        num_classes=len(CLASS_NAMES),
        use_lbp=use_lbp,
        lbp_in_dim=lbp_in_dim
    )

    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        state_dict = ckpt["model_state_dict"]
    else:
        state_dict = ckpt

    model.load_state_dict(state_dict, strict=True)

    model.eval()
    return model.to(DEVICE)


def predict_image(pil_img, model, cfg):
    x = img_transform(pil_img).unsqueeze(0).to(DEVICE)

    lbp = None
    if cfg["use_lbp"]:
        lbp = extract_lbp_features(
            pil_img,
            cfg["lbp_mode"],
            cfg["lbp_in_dim"]
        ).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(x, lbp)
        probs = F.softmax(logits, dim=1).squeeze(0)

    confs, idxs = torch.topk(probs, k=len(CLASS_NAMES))

    results = []
    for conf, idx in zip(confs.tolist(), idxs.tolist()):
        label = CLASS_NAMES[idx]
        results.append((label, float(conf)))

    return results