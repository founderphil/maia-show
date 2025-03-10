# backend/models/vision/vision.py

import cv2
import numpy as np
import mediapipe as mp
from fer import FER
import time
import os

def capture_webcam_image(save_path="captured.png"):
    if save_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(base_dir, "..", "..", "frontend", "captured.png")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam")
        return None

    time.sleep(1)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 1.0)   
    cap.set(cv2.CAP_PROP_EXPOSURE, -4)    

    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite(save_path, frame)
        print(f"Image captured and saved to {save_path}")
        return save_path
    else:
        print("Failed to capture image from webcam")
        return None

def detect_emotion(image):
    detector = FER(mtcnn=True)
    results = detector.detect_emotions(image)
    if results:
        emotions = results[0]["emotions"]
        primary_emotion = max(emotions, key=emotions.get)
        return primary_emotion
    else:
        return "No face detected"

def detect_posture(image):
    mp_pose = mp.solutions.pose
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            avg_hip = (left_hip.y + right_hip.y) / 2
            avg_shoulder = (left_shoulder.y + right_shoulder.y) / 2
            if (avg_hip - avg_shoulder) < 0.1:
                return "Sitting"
            else:
                return "Standing"
        else:
            return "No pose detected"

def detect_vision(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return {"emotion": "Image not found", "posture": "N/A"}
    emotion = detect_emotion(image)
    posture = detect_posture(image)
    return {"emotion": emotion, "posture": posture}

if __name__ == "__main__":
    captured_path = capture_webcam_image() 
    if captured_path:
        result = detect_vision(captured_path)
        print("Detected:", result)