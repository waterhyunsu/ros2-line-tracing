import cv2
import numpy as np


# 웹캠 초기화
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()


# P 제어 상수
KP = 0.005

while True:
    ret, frame = cap.read()

    if not ret:
        print("웹캠 영상을 읽을 수 없습니다.")
        break

    # 1. BGR -> HSV 변환
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 2. 빨간색 영역 마스킹
    # 빨간색은 HSV 색상 범위가 두 구간으로 나뉨
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask = mask1 | mask2

    # 3. 영상 크기 및 중앙 좌표 계산
    height, width = frame.shape[:2]
    image_center_x = width // 2
    image_center_y = height // 2

    # 영상 중앙 표시
    cv2.line(
        frame,
        (image_center_x, 0),
        (image_center_x, height),
        (0, 255, 0),
        2
    )

    cv2.circle(
        frame,
        (image_center_x, image_center_y),
        5,
        (0, 255, 0),
        -1
    )

    # 4. 빨간색 영역의 중심점 계산
    M = cv2.moments(mask)

    if M["m00"] > 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # 5. 영상 중앙과 빨간색 중심의 오차 계산
        error = cx - image_center_x

        # 6. P 제어로 회전 속도 계산
        angular_z = -KP * error

        # 회전 속도 제한
        angular_z = max(-1.0, min(1.0, angular_z))

        # 빨간색 중심점 표시
        cv2.circle(
            frame,
            (cx, cy),
            8,
            (255, 0, 0),
            -1
        )

        # 빨간색 중심점과 영상 중앙 연결
        cv2.line(
            frame,
            (image_center_x, image_center_y),
            (cx, cy),
            (255, 255, 0),
            2
        )

        # 화면에 결과 표시
        cv2.putText(
            frame,
            f"Error: {error}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Angular Z: {angular_z:.3f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # 터미널 출력
        print(
            f"cx={cx}, "
            f"center={image_center_x}, "
            f"error={error}, "
            f"angular_z={angular_z:.3f}"
        )

    else:
        # 빨간색이 검출되지 않은 경우
        cv2.putText(
            frame,
            "Red line not detected",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

    # 7. 영상 출력
    cv2.imshow("Line Tracking", frame)
    cv2.imshow("Red Mask", mask)

    # q 키로 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# 자원 해제
cap.release()
cv2.destroyAllWindows()