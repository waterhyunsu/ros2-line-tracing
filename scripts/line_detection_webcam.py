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

    # BGR -> HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 빨간색은 HSV에서 0도 부근과 180도 부근으로 나뉨
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask = mask1 | mask2

    # Moment 계산
    M = cv2.moments(mask)

    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # 빨간 영역 중심점
        cv2.circle(frame, (cx, cy), 10, (255, 0, 0), -1)

        # 중심점 좌표 출력
        cv2.putText(
            frame,
            f"Line Center: ({cx}, {cy})",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    # 영상의 중앙점
    height, width = frame.shape[:2]
    image_center_x = width // 2
    image_center_y = height // 2

    cv2.circle(
        frame,
        (image_center_x, image_center_y),
        10,
        (0, 255, 0),
        -1
    )

    # 화면 중앙 세로선
    cv2.line(
        frame,
        (image_center_x, 0),
        (image_center_x, height),
        (0, 255, 0),
        2
    )

    cv2.imshow("Line Detection", frame)
    cv2.imshow("Red Mask", mask)

    # q 키로 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()