"""Rasm bilan ishlash (OpenCV): chiptadagi QR kodni o'qish va profil suratida yuz borligini tekshirish."""
import os

import cv2
import numpy as np

_FACE = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))


def has_face(image_bytes: bytes) -> bool:
    """Suratda kamida bitta yuz bormi (guvohnoma uchun)."""
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False
    scale = 800 / max(img.shape)
    if scale < 1:
        img = cv2.resize(img, None, fx=scale, fy=scale)
    img = cv2.equalizeHist(img)
    side = min(img.shape)
    faces = _FACE.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(side // 8, side // 8))
    return len(faces) > 0


def decode(image_bytes: bytes) -> str | None:
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    detector = cv2.QRCodeDetector()
    # Asl o'lcham, keyin kattalashtirilgan va kulrang variant — telefon kamerasidagi suratlar uchun
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for candidate in (img, gray, cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)):
        text, _, _ = detector.detectAndDecode(candidate)
        if text:
            return text
    return None
