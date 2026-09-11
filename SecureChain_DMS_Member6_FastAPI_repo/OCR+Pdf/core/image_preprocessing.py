"""
core/image_preprocessing.py
----------------------------
Member 6 scope: "OCR/document classification" ke pehle document ko
readable banana — blur detect karo, agar blurred hai to sharpen +
contrast-enhance karo, taaki Qwen OCR accha result de.
"""

import cv2
import numpy as np
import os


class DocumentDeblurEngine:
    def __init__(self, blur_threshold: float = 120.0):
        # Laplacian variance threshold: isse kam ho to image "blurred" maani jaati hai
        self.blur_threshold = blur_threshold

    def measure_blur(self, gray_img: np.ndarray) -> float:
        """Laplacian variance -> low value = zyada blur"""
        return cv2.Laplacian(gray_img, cv2.CV_64F).var()

    def unsharp_mask(self, img: np.ndarray, sigma: float = 1.5, strength: float = 1.6) -> np.ndarray:
        blurred = cv2.GaussianBlur(img, (0, 0), sigma)
        sharpened = cv2.addWeighted(img, strength, blurred, -(strength - 1), 0)
        return sharpened

    def enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """CLAHE - handwriting / faded stamps ko readable banata hai"""
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l2 = clahe.apply(l)
        merged = cv2.merge((l2, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    def denoise(self, img: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)

    def process(self, image_path: str, output_path: str = None) -> dict:
        """
        Full pipeline: blur measure -> (agar blurred) denoise -> sharpen -> contrast enhance.
        Returns dict with path to the cleaned image + diagnostics.
        """
        img = cv2.imread(image_path)
        if img is None:
            return {"error": f"Could not read image at {image_path}"}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = self.measure_blur(gray)
        # FIX: numpy comparisons return numpy.bool_, which json.dumps() can't serialize.
        # Cast explicitly to native Python bool.
        was_blurred = bool(blur_score < self.blur_threshold)

        processed = img.copy()
        if was_blurred:
            processed = self.denoise(processed)
            processed = self.unsharp_mask(processed)

        # Contrast enhancement helps even on non-blurred low-quality scans (faded FIR stamps etc.)
        processed = self.enhance_contrast(processed)

        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_deblurred.jpg"

        cv2.imwrite(output_path, processed)

        return {
            "output_path": output_path,
            "blur_score": round(float(blur_score), 2),
            "was_blurred": was_blurred,
            "threshold_used": self.blur_threshold,
        }
