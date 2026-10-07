import cv2
import numpy as np

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("웹캠 영상을 읽을 수 없습니다.")
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 빨간색 HSV 범위
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 | mask2

    height, width = frame.shape[:2]
    image_center_x = width // 2

    M = cv2.moments(mask)

    if M["m00"] > 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # 영상 중앙과 빨간색 중심의 가로 오차
        error = cx - image_center_x

        # 빨간색 중심점
        cv2.circle(frame, (cx, cy), 8, (255, 0, 0), -1)

        # 오차 표시
        cv2.putText(
            frame,
            f"Error: {error}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        print(f"cx={cx}, center={image_center_x}, error={error}")

    else:
        # 빨간색이 검출되지 않은 경우
        cv2.putText(
            frame,
            "Red line not detected",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    # 영상 중앙 표시
    cv2.line(
        frame,
        (image_center_x, 0),
        (image_center_x, height),
        (0, 255, 0),
        2
    )

    cv2.imshow("Line Tracking", frame)
    cv2.imshow("Red Mask", mask)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()