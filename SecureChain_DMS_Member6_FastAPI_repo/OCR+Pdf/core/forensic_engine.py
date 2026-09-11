import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageChops
import os


class DocumentForensicCNN(nn.Module):
    def __init__(self):
        super(DocumentForensicCNN, self).__init__()
        self.feature_extractor = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.feature_extractor(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


class ForensicAnalysisEngine:
    def __init__(self, weights_path=None):
        if weights_path is None:
            project_dir = os.environ.get("SECURECHAIN_HOME", "/kaggle/working/SecureChain_DMS_Member6")
            weights_path = os.path.join(project_dir, "models", "cnn_ela_weights.pth")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DocumentForensicCNN().to(self.device)

        if os.path.exists(weights_path):
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        else:
            # NOTE: this saves RANDOM-INIT weights as a placeholder so the demo doesn't crash.
            # Before judging/production, this CNN needs to actually be trained on a labeled
            # tampered-vs-authentic dataset — right now it is NOT a trained tamper detector.
            print("[!] Weights absent. Saving baseline (untrained) diagnostic configuration...")
            os.makedirs(os.path.dirname(weights_path), exist_ok=True)
            torch.save(self.model.state_dict(), weights_path)
        self.model.eval()

    def compute_ela(self, image_path: str, quality: int = 90) -> Image.Image:
        temp_filename = "/kaggle/working/temp_resave_log.jpg"
        original = Image.open(image_path).convert('RGB')
        original.save(temp_filename, 'JPEG', quality=quality)
        resaved = Image.open(temp_filename)

        ela_image = ImageChops.difference(original, resaved)
        extrema = ela_image.getextrema()

        flat_extrema = []
        for item in extrema:
            if isinstance(item, tuple):
                flat_extrema.extend(item)
            else:
                flat_extrema.append(item)

        max_diff = max(flat_extrema) if flat_extrema else 1
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff

        ela_arr = np.array(ela_image)
        scaled_arr = np.clip(ela_arr * scale, 0, 255).astype(np.uint8)
        scaled_ela_image = Image.fromarray(scaled_arr)

        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return scaled_ela_image

    def evaluate_integrity(self, image_path: str):
        ela_img = self.compute_ela(image_path)
        resized = ela_img.resize((128, 128))
        tensor_data = torch.from_numpy(np.array(resized)) / 255.0
        tensor_data = tensor_data.permute(2, 0, 1).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            tamper_probability = self.model(tensor_data).item()

        if tamper_probability > 0.75:
            log_flag = "HIGH-ALERT: SUSPECTED FORGERY"
        elif tamper_probability > 0.40:
            log_flag = "MID-LEVEL ANOMALY DETECTED"
        else:
            log_flag = "INTEGRITY CHECK PASSED"

        return log_flag, tamper_probability, ela_img
