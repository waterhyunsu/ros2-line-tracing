````markdown
# ROS 2 TurtleBot3 Red Line Tracer

TurtleBot3 Waffle Pi의 카메라를 이용하여 Gazebo 환경에서 빨간색 라인을 검출하고, 검출된 라인의 중심 위치를 기반으로 TurtleBot3가 자동으로 라인을 따라가도록 구현한 ROS 2 프로젝트입니다.

Windows 환경에서 OpenCV를 이용한 레드라인 검출 프로토타입을 먼저 구현한 후, ROS 2와 Gazebo 환경으로 확장했습니다.

---

## 1. Project Overview

### 프로젝트 목표

- TurtleBot3 Waffle Pi 카메라 영상 수신
- ROS 2 Image 메시지를 OpenCV 영상으로 변환
- HSV 기반 빨간색 라인 검출
- 검출된 라인의 중심점 계산
- 화면 중심과 라인 중심의 오차 계산
- P 제어를 이용한 회전 속도 계산
- `/cmd_vel`을 통한 TurtleBot3 주행 제어
- 라인 위치에 따른 주행 속도 조절
- 레드라인 미검출 시 자동 정지
- Gazebo 시뮬레이션 환경에서 자율주행 검증

### 전체 동작 구조

```text
TurtleBot3 Camera
       ↓
/camera/image_raw
       ↓
cv_bridge
       ↓
OpenCV
       ↓
HSV Red Line Detection
       ↓
Centroid (CX)
       ↓
Error Calculation
       ↓
P Controller
       ↓
Twist
       ↓
/cmd_vel
       ↓
TurtleBot3
````

---

## 2. Development Environment

| 항목                   | 환경                   |
| -------------------- | -------------------- |
| OS                   | Ubuntu 22.04         |
| ROS                  | ROS 2 Humble         |
| Simulation           | Gazebo Classic 11    |
| Robot                | TurtleBot3 Waffle Pi |
| Language             | Python               |
| Image Processing     | OpenCV               |
| ROS Image Conversion | cv_bridge            |
| Version Control      | Git / GitHub         |

---

## 3. Camera Topic Subscription

TurtleBot3 Gazebo에서 제공하는 카메라 토픽을 구독합니다.

```text
/camera/image_raw
```

ROS 2의 `sensor_msgs/msg/Image` 메시지를 구독하여 카메라 영상을 수신합니다.

---

## 4. ROS Image → OpenCV

`cv_bridge`를 사용하여 ROS 2 Image 메시지를 OpenCV 이미지로 변환합니다.

```python
frame = self.bridge.imgmsg_to_cv2(
    msg,
    desired_encoding='bgr8'
)
```

변환된 영상을 OpenCV를 이용하여 처리합니다.

---

## 5. Gazebo Red Line Track

Gazebo에서 별도의 `track1` 모델을 생성하여 레드라인 트랙을 구성했습니다.

트랙 모델은 다음 경로에 저장하여 사용할 수 있습니다.

```text
~/.gazebo/models/track1
```

Gazebo 실행 후 다음 명령으로 트랙을 추가합니다.

```bash
ros2 run gazebo_ros spawn_entity.py \
  -entity track1 \
  -file ~/.gazebo/models/track1/model.sdf \
  -x 0 \
  -y 0 \
  -z 0
```

현재 트랙은 Gazebo World에 직접 포함하지 않고 별도의 모델로 spawn하는 방식입니다.

---

## 6. HSV 기반 Red Line Detection

카메라 영상을 BGR에서 HSV 색 공간으로 변환한 후 빨간색 영역을 검출합니다.

빨간색은 HSV 색 공간에서 양 끝 영역에 분포할 수 있기 때문에 두 개의 범위를 사용합니다.

```python
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])

lower_red2 = np.array([170, 100, 100])
upper_red2 = np.array([180, 255, 255])
```

두 개의 Mask를 결합하여 최종적인 Red Mask를 생성합니다.

```python
red_mask = mask1 | mask2
```

---

## 7. Red Line Center Detection

OpenCV의 `moments()`를 이용하여 검출된 빨간색 영역의 중심점을 계산합니다.

```python
moments = cv2.moments(red_mask)

cx = int(moments['m10'] / moments['m00'])
cy = int(moments['m01'] / moments['m00'])
```

여기서 `cx`를 레드라인의 화면상 중심 X 좌표로 사용합니다.

카메라 영상의 중심 X 좌표와 비교하여 주행 오차를 계산합니다.

```text
Error = CX - Image Center
```

---

## 8. P Controller

레드라인 중심과 이미지 중심의 오차를 이용하여 TurtleBot3의 회전 속도를 계산합니다.

```python
KP = 0.005

angular_z = -KP * error
```

계산된 각속도는 다음 범위로 제한합니다.

```python
angular_z = max(
    -1.0,
    min(1.0, angular_z)
)
```

### 제어 원리

```text
라인이 왼쪽
    ↓
Error < 0
    ↓
Angular Z > 0

라인이 오른쪽
    ↓
Error > 0
    ↓
Angular Z < 0

라인이 중앙
    ↓
Error ≈ 0
    ↓
Angular Z ≈ 0
```

---

## 9. `/cmd_vel` 기반 TurtleBot3 주행

계산된 선속도와 각속도를 `geometry_msgs/msg/Twist` 메시지에 저장합니다.

```python
cmd = Twist()

cmd.linear.x = linear_x
cmd.angular.z = angular_z

self.cmd_vel_publisher.publish(cmd)
```

`/cmd_vel`은 TurtleBot3에 속도 명령을 전달하는 ROS 2 토픽입니다.

```text
line_tracer_node
       ↓
     Twist
       ↓
    /cmd_vel
       ↓
   TurtleBot3
       ↓
     Motor
```

### 속도 명령

* `linear.x` : 전진/후진 속도
* `angular.z` : 회전 속도

---

## 10. Error-based Speed Control

레드라인 중심과 이미지 중심의 오차 크기에 따라 선속도를 조절합니다.

```python
if abs(error) <= 30:
    linear_x = 0.10
elif abs(error) <= 80:
    linear_x = 0.07
else:
    linear_x = 0.05
```

| Error | Linear Velocity |       |          |
| ----: | --------------: | ----- | -------- |
|     ` |           error | ≤ 30` | 0.10 m/s |
|     ` |           error | ≤ 80` | 0.07 m/s |
|     ` |           error | > 80` | 0.05 m/s |

라인이 화면 중앙에 가까울수록 빠르게 주행하고, 라인에서 크게 벗어날수록 속도를 낮춥니다.

---

## 11. Red Line Not Found → Stop

레드라인이 검출되지 않는 경우 정지 명령을 `/cmd_vel`로 발행합니다.

```python
cmd = Twist()

cmd.linear.x = 0.0
cmd.angular.z = 0.0

self.cmd_vel_publisher.publish(cmd)
```

이를 통해 레드라인을 놓쳤을 때 이전 속도 명령이 계속 유지되는 것을 방지합니다.

```text
Red Line Detected
       ↓
   Autonomous
     Driving

Red Line Not Found
       ↓
linear.x = 0.0
angular.z = 0.0
       ↓
      Stop
```

---

## 12. Development Progress

* [x] ROS 2 Python 패키지 생성
* [x] `/camera/image_raw` 카메라 토픽 구독
* [x] ROS Image → OpenCV 변환
* [x] Gazebo TurtleBot3 카메라 확인
* [x] Gazebo 레드라인 트랙 모델 구성
* [x] HSV 기반 레드라인 검출
* [x] 레드라인 중심점 계산
* [x] 이미지 중심과 레드라인 중심의 오차 계산
* [x] P 제어 기반 각속도 계산
* [x] `/cmd_vel` 기반 TurtleBot3 주행
* [x] 레드라인 미검출 시 정지
* [x] 오차 기반 선속도 제어
* [x] Gazebo 자동 주행 테스트
* [x] GitHub 저장소 구축 및 버전 관리

---

## 13. Repository Structure

```text
ros2-line-tracing/
├── .gitignore
├── README.md
│
├── scripts/
│   └── line_detection_webcam.py
│
└── ros2_ws/
    └── src/
        └── line_tracer/
            ├── line_tracer/
            │   ├── __init__.py
            │   └── line_tracer_node.py
            │
            ├── resource/
            │   └── line_tracer
            │
            ├── test/
            │   ├── test_copyright.py
            │   ├── test_flake8.py
            │   └── test_pep257.py
            │
            ├── package.xml
            ├── setup.cfg
            └── setup.py
```

---

## 14. Run

### 1. ROS 2 환경 설정

```bash
source /opt/ros/humble/setup.bash
```

### 2. TurtleBot3 모델 설정

```bash
export TURTLEBOT3_MODEL=waffle_pi
```

### 3. Gazebo 실행

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

### 4. Red Line Track Spawn

새 터미널에서:

```bash
source /opt/ros/humble/setup.bash

ros2 run gazebo_ros spawn_entity.py \
  -entity track1 \
  -file ~/.gazebo/models/track1/model.sdf \
  -x 0 \
  -y 0 \
  -z 0
```

### 5. ROS 2 Workspace Build

```bash
cd /mnt/c/01_YoonHyunsu/14_ROS2/ros2-line-tracing/ros2_ws

colcon build --symlink-install

source install/setup.bash
```

### 6. Red Line Tracer 실행

```bash
ros2 run line_tracer line_tracer_node
```

실행하면 OpenCV 창을 통해 레드라인 검출 결과와 제어값을 확인할 수 있습니다.

```text
CX: 320  Error: 0
Linear: 0.10  Angular: -0.000
```

---

## 15. Development History

### 1. OpenCV Webcam Prototype

Windows 환경에서 USB Webcam을 이용하여 먼저 레드라인 검출 알고리즘을 구현했습니다.

```text
Webcam
  ↓
OpenCV
  ↓
HSV
  ↓
Red Detection
  ↓
Centroid
  ↓
Error
```

초기 프로토타입에서는 ROS 2를 사용하지 않고 영상 처리 및 중심점 계산 로직을 검증했습니다.

### 2. ROS 2 Camera Integration

기존 OpenCV 프로토타입을 ROS 2 환경으로 확장했습니다.

```text
TurtleBot3 Camera
      ↓
/camera/image_raw
      ↓
cv_bridge
      ↓
OpenCV
```

### 3. Gazebo Simulation

TurtleBot3 Waffle Pi의 Gazebo 카메라를 이용하여 실제 로봇 없이 카메라 기반 레드라인 검출을 테스트했습니다.

### 4. Autonomous Line Following

레드라인 중심 오차를 P 제어에 적용하고 `/cmd_vel`을 통해 TurtleBot3의 선속도와 각속도를 제어했습니다.

최종적으로 Gazebo 환경에서 레드라인을 따라 자동 주행하는 것을 확인했습니다.

---

## 16. Project Result

최종적으로 다음과 같은 카메라 기반 자율주행 파이프라인을 구현했습니다.

```text
Camera
  ↓
ROS 2 Image Topic
  ↓
cv_bridge
  ↓
OpenCV / HSV
  ↓
Red Line Detection
  ↓
Centroid Detection
  ↓
Error Calculation
  ↓
P Controller
  ↓
Linear / Angular Velocity
  ↓
Twist
  ↓
/cmd_vel
  ↓
TurtleBot3
```

Gazebo 시뮬레이션에서 TurtleBot3 Waffle Pi가 카메라로 레드라인을 검출하고, 중심 오차에 따라 방향과 속도를 조절하면서 자동으로 주행하는 것을 검증했습니다.

---

## 17. Future Improvements

현재 기본적인 레드라인 추종 기능을 구현한 상태이며, 향후 다음과 같은 기능을 추가할 수 있습니다.

* ROI(Region of Interest) 기반 검출
* 노이즈 제거 및 Morphological Filtering
* PID Controller 적용
* 곡선 구간 주행 성능 개선
* 장애물 회피
* 실제 TurtleBot3 Waffle Pi 적용
* 주행 파라미터 최적화

````
