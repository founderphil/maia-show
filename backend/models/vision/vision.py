import cv2
import numpy as np
import mediapipe as mp
from fer import FER
import time
import os

def capture_webcam_image(save_path=None):
    if save_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(base_dir, "..", "..", "static", "captured.png")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

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
        print(f"✅ Image captured and saved to {save_path}")
        return save_path
    else:
        print("❌ Failed to capture image from webcam")
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
    import math
    mp_pose = mp.solutions.pose
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            left_knee = landmarks[25]
            right_knee = landmarks[26]

            # Draw landmarks
            mp_drawing = mp.solutions.drawing_utils
            mp_pose_module = mp.solutions.pose
            annotated_image = image.copy()
            mp_drawing.draw_landmarks(
                annotated_image,
                results.pose_landmarks,
                mp_pose_module.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0,0,255), thickness=2, circle_radius=2)
            )
            annotated_path = os.path.join(os.path.dirname(__file__), "captured_landmarks.png")
            cv2.imwrite(annotated_path, annotated_image)
            print(f"✅ Landmarks image saved to {annotated_path}")

            def get_angle(a, b, c):
                ab = np.array([a.x - b.x, a.y - b.y])
                cb = np.array([c.x - b.x, c.y - b.y])
                cosine_angle = np.dot(ab, cb) / (np.linalg.norm(ab) * np.linalg.norm(cb) + 1e-6)
                angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
                return np.degrees(angle)

            left_hip_angle = get_angle(left_shoulder, left_hip, left_knee)
            right_hip_angle = get_angle(right_shoulder, right_hip, right_knee)
            avg_hip_angle = (left_hip_angle + right_hip_angle) / 2

            print("Landmarks:")
            print(f"  Left Shoulder: (x={left_shoulder.x:.3f}, y={left_shoulder.y:.3f})")
            print(f"  Left Hip:      (x={left_hip.x:.3f}, y={left_hip.y:.3f})")
            print(f"  Left Knee:     (x={left_knee.x:.3f}, y={left_knee.y:.3f})")
            print(f"  Right Shoulder: (x={right_shoulder.x:.3f}, y={right_shoulder.y:.3f})")
            print(f"  Right Hip:      (x={right_hip.x:.3f}, y={right_hip.y:.3f})")
            print(f"  Right Knee:     (x={right_knee.x:.3f}, y={right_knee.y:.3f})")
            print(f"Angles:")
            print(f"  Left Hip Angle: {left_hip_angle:.2f}")
            print(f"  Right Hip Angle: {right_hip_angle:.2f}")
            print(f"  Avg Hip Angle: {avg_hip_angle:.2f}")

            if avg_hip_angle <= 155: # hugely important number to get right. seems standing has not gone below 158.0, straight on is 170+
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
