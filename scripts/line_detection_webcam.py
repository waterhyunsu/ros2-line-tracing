import cv2
import numpy as np


# ==============================
# 설정값
# ==============================

CAMERA_INDEX = 0

KP = 0.005

MAX_ANGULAR_Z = 1.0

SPEED_FAST = 0.15
SPEED_MEDIUM = 0.10
SPEED_SLOW = 0.05


def main():
    # 웹캠 연결
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("Error: 웹캠을 열 수 없습니다.")
        return

    print("웹캠 연결 성공")
    print("종료하려면 'q' 키를 누르세요.")

    while True:
        # 영상 읽기
        ret, frame = cap.read()

        if not ret:
            print("\nError: 카메라 영상을 읽을 수 없습니다.")
            break

        height, width = frame.shape[:2]

        # 영상 중심 좌표
        image_center_x = width // 2
        image_center_y = height // 2

        # ==============================
        # 1. 빨간색 라인 검출
        # ==============================

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # HSV 색상 범위
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])

        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        # 빨간색 마스크 생성
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

        mask = cv2.bitwise_or(mask1, mask2)

        # ==============================
        # 2. 중심점 및 제어값 초기화
        # ==============================

        line_detected = False

        cx = None
        cy = None
        error = None

        # 검출 실패 시 정지값
        linear_x = 0.0
        angular_z = 0.0

        # ==============================
        # 3. 빨간색 라인 중심점 계산
        # ==============================

        M = cv2.moments(mask)

        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            line_detected = True

            # ==============================
            # 4. 중심 오차 계산
            # ==============================

            error = cx - image_center_x

            # ==============================
            # 5. P 제어로 회전 속도 계산
            # ==============================

            angular_z = -KP * error

            # 회전 속도 제한
            angular_z = max(
                -MAX_ANGULAR_Z,
                min(MAX_ANGULAR_Z, angular_z)
            )

            # ==============================
            # 6. 오차에 따른 전진 속도 조절
            # ==============================

            if abs(error) <= 30:
                linear_x = SPEED_FAST

            elif abs(error) <= 80:
                linear_x = SPEED_MEDIUM

            else:
                linear_x = SPEED_SLOW

        # ==============================
        # 7. 영상 시각화
        # ==============================

        # 영상 중심선
        cv2.line(
            frame,
            (image_center_x, 0),
            (image_center_x, height),
            (255, 255, 255),
            2
        )

        if line_detected:
            # 검출된 라인 중심점
            cv2.circle(
                frame,
                (cx, cy),
                8,
                (0, 255, 0),
                -1
            )

            # 영상 중심과 라인 중심 연결
            cv2.line(
                frame,
                (image_center_x, image_center_y),
                (cx, cy),
                (255, 0, 0),
                2
            )

            cv2.putText(
                frame,
                f"Error: {error} px",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Linear X: {linear_x:.2f} m/s",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Angular Z: {angular_z:.3f} rad/s",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            status = "LINE DETECTED"

        else:
            cv2.putText(
                frame,
                "LINE NOT DETECTED - STOP",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

            status = "STOP"

        # 터미널 상태 출력
        if line_detected:
            print(
                f"\rError={error:5d} | "
                f"Linear X={linear_x:.2f} | "
                f"Angular Z={angular_z:.3f} | "
                f"{status}       ",
                end="",
                flush=True
            )
        else:
            print(
                "\r라인 미검출 | Linear X=0.00 | "
                "Angular Z=0.000 | STOP       ",
                end="",
                flush=True
            )

        # 영상 표시
        cv2.imshow("Line Detection", frame)
        cv2.imshow("Red Mask", mask)

        # q 키로 종료
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()

    print("\n프로그램 종료")


if __name__ == "__main__":
    main()