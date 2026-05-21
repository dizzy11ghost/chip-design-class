import cv2
import numpy as np

# ================= CONFIG =================
desired_aruco_dictionary = "DICT_ARUCO_ORIGINAL"
marker_length = 0.06   # metros (5 cm)
pixel_size = 1.12e-6   # metros
focal_length_px = 500  # en pixeles
camera_index = 0

# Convertir focal a metros
focal_length_m = focal_length_px * pixel_size

ARUCO_DICT = {
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL
}

aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[desired_aruco_dictionary])
aruco_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

print("Presiona ESC para salir")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    corners, ids, _ = detector.detectMarkers(frame)

    if ids is not None:
        ids = ids.flatten()

        for (marker_corner, marker_id) in zip(corners, ids):
            pts = marker_corner.reshape((4, 2))

            (top_left, top_right, bottom_right, bottom_left) = pts

            top_left = tuple(map(int, top_left))
            top_right = tuple(map(int, top_right))
            bottom_right = tuple(map(int, bottom_right))
            bottom_left = tuple(map(int, bottom_left))

            # ================= DISTANCIA =================
            width_px = np.linalg.norm(np.array(top_right) - np.array(top_left))

            # convertir ancho en metros (sensor)
            width_m = width_px * pixel_size

            # Z = f * X / x
            distance = (focal_length_m * marker_length) / width_m
            # ============================================

            # Centro
            center_x = int((top_left[0] + bottom_right[0]) / 2)
            center_y = int((top_left[1] + bottom_right[1]) / 2)

            # Dibujar
            cv2.line(frame, top_left, top_right, (255, 105, 180), 2)
            cv2.line(frame, top_right, bottom_right, (138, 43, 226), 2)
            cv2.line(frame, bottom_right, bottom_left, (135, 206, 250), 2)
            cv2.line(frame, bottom_left, top_left, (255, 182, 193), 2)

            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

            # Texto
            cv2.putText(frame,
                        f"ID: {marker_id}",
                        (top_left[0], top_left[1] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 255), 2)

            cv2.putText(frame,
                        f"{distance:.2f} m",
                        (top_left[0], top_left[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

    cv2.imshow("Aruco + Distancia REAL", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
