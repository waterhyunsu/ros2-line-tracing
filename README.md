
````markdown
# ROS 2 TurtleBot3 Red Line Tracer

ROS 2와 TurtleBot3 Waffle Pi를 활용한 레드라인 트레이서 개인 프로젝트입니다.

Gazebo 시뮬레이션 환경에서 TurtleBot3의 카메라 영상을 ROS 2 토픽으로 수신하고,
OpenCV를 이용해 빨간색 라인을 검출한 뒤 라인의 위치를 기반으로 로봇의 주행 방향을 제어하는 것을 목표로 합니다.

---

## 1. Project Overview

| 항목 | 내용 |
|---|---|
| Project | TurtleBot3 Red Line Tracer |
| Platform | TurtleBot3 Waffle Pi |
| ROS | ROS 2 Humble |
| OS | Ubuntu 22.04 |
| Simulation | Gazebo Classic 11 |
| Language | Python |
| Computer Vision | OpenCV |
| ROS Image Conversion | cv_bridge |
| Version Control | Git / GitHub |

본 프로젝트는 실제 로봇 주행에 앞서 Gazebo 시뮬레이션 환경에서
카메라 기반 라인 트레이싱 알고리즘을 구현하고 검증하는 것을 목적으로 합니다.

---

## 2. Project Goal

TurtleBot3에 장착된 카메라를 이용하여 바닥의 빨간색 라인을 실시간으로 인식하고,
라인의 중심 위치와 카메라 화면의 중심 사이의 오차를 계산하여
TurtleBot3가 라인을 따라 주행하도록 구현합니다.

최종 목표는 다음과 같은 ROS 2 기반 자율주행 파이프라인을 구축하는 것입니다.

```text
Gazebo
   ↓
TurtleBot3 Waffle Pi Camera
   ↓
/camera/image_raw
   ↓
ROS 2 line_tracer_node
   ↓
cv_bridge
   ↓
OpenCV
   ↓
Red Line Detection
   ↓
Line Center Detection
   ↓
Error Calculation
   ↓
P Controller
   ↓
/cmd_vel
   ↓
TurtleBot3 Line Following
````

---

## 3. Current Implementation

현재까지 다음 기능을 구현하고 검증했습니다.

### 3.1 ROS 2 Python Package

ROS 2 `ament_python` 기반의 `line_tracer` 패키지를 구성했습니다.

```text
ros2_ws/
└── src/
    └── line_tracer/
        ├── line_tracer/
        │   ├── __init__.py
        │   └── line_tracer_node.py
        ├── resource/
        │   └── line_tracer
        ├── test/
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```

---

### 3.2 Camera Topic Subscription

TurtleBot3 Gazebo 카메라에서 발행되는

```text
/camera/image_raw
```

토픽을 `sensor_msgs/msg/Image` 타입으로 구독합니다.

```python
self.subscription = self.create_subscription(
    Image,
    '/camera/image_raw',
    self.image_callback,
    10
)
```

카메라 토픽을 정상적으로 수신하고 이미지 해상도를 확인했습니다.

---

### 3.3 ROS Image → OpenCV Conversion

`cv_bridge`를 이용하여 ROS 2 Image 메시지를 OpenCV의 BGR 이미지로 변환합니다.

```python
frame = self.bridge.imgmsg_to_cv2(
    msg,
    desired_encoding='bgr8'
)
```

이를 통해 ROS 2 카메라 데이터를 OpenCV 영상 처리 파이프라인으로 연결했습니다.

---

### 3.4 Gazebo TurtleBot3 Camera

Gazebo Classic 환경에서 TurtleBot3 Waffle Pi를 실행하고
카메라 토픽을 확인했습니다.

카메라 영상은 약 10 Hz 이상의 주기로 정상적으로 발행되는 것을 확인했습니다.

```text
/camera/image_raw
```

---

### 3.5 Gazebo Red Line Track

Gazebo에서 사용할 수 있는 별도의 트랙 모델을 추가하여
TurtleBot3 카메라가 라인을 인식할 수 있는 시뮬레이션 환경을 구성했습니다.

트랙 모델은 Gazebo의 SDF 모델로 구성되어 있으며,
프로젝트 목적에 맞게 여러 색상의 선분을 빨간색으로 통일했습니다.

현재 구조:

```text
Gazebo World
├── TurtleBot3 Waffle Pi
│   └── Camera
│
└── Red Line Track
```

---

### 3.6 Red Line Detection

OpenCV와 HSV 색 공간을 이용하여 빨간색 영역을 검출합니다.

빨간색은 HSV 색 공간에서 Hue가 양 끝 영역에 걸쳐 있기 때문에
두 개의 범위를 사용합니다.

```python
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])

lower_red2 = np.array([170, 100, 100])
upper_red2 = np.array([180, 255, 255])
```

두 영역의 Mask를 결합하여 최종적인 빨간색 검출 Mask를 생성합니다.

```python
mask1 = cv2.inRange(
    hsv,
    lower_red1,
    upper_red1
)

mask2 = cv2.inRange(
    hsv,
    lower_red2,
    upper_red2
)

red_mask = mask1 | mask2
```

---

### 3.7 Line Center Detection

OpenCV의 Image Moment를 이용하여 검출된 빨간색 영역의 중심 좌표를 계산합니다.

```python
moments = cv2.moments(red_mask)

cx = int(moments['m10'] / moments['m00'])
cy = int(moments['m01'] / moments['m00'])
```

계산된 중심점은 카메라 영상에 표시하여
검출 결과를 시각적으로 확인할 수 있도록 구성했습니다.

---

### 3.8 Error Calculation

검출된 빨간색 라인의 중심 X 좌표와
카메라 영상의 중앙 X 좌표를 비교하여 오차를 계산합니다.

```python
image_center_x = frame.shape[1] // 2

error = cx - image_center_x
```

이 `error` 값은 이후 TurtleBot3의 회전 속도를 결정하는
제어 입력으로 사용합니다.

---

## 4. Development Progress

### Completed

* [x] GitHub 프로젝트 구성
* [x] ROS 2 Humble 개발환경 구성
* [x] ROS 2 Python package 생성
* [x] TurtleBot3 Waffle Pi Gazebo 환경 구성
* [x] `/camera/image_raw` 토픽 확인
* [x] ROS 2 Camera Topic Subscription
* [x] `cv_bridge`를 이용한 OpenCV 변환
* [x] Gazebo Red Line Track 모델 추가
* [x] Red Line HSV Color Detection
* [x] Red Line Mask 생성
* [x] Red Line Center Detection
* [x] Line Center Error Calculation

### In Progress

* [ ] P Controller 기반 조향 제어
* [ ] `/cmd_vel` Publisher 구현
* [ ] 선 검출 결과 기반 TurtleBot3 회전 제어
* [ ] 직선 및 곡선 구간 주행 테스트
* [ ] 제어 파라미터 튜닝
* [ ] 라인 이탈 상황 처리

### Final Goal

* [ ] Gazebo Red Line Autonomous Driving
* [ ] 안정적인 라인 트레이싱
* [ ] 다양한 트랙 구간 테스트
* [ ] 최종 주행 성능 검증

---

## 5. Repository Structure

```text
ros2-line-tracing/
│
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

## 6. Development Environment

```text
OS
└── Ubuntu 22.04

ROS
└── ROS 2 Humble

Simulation
└── Gazebo Classic 11

Robot
└── TurtleBot3 Waffle Pi

Language
└── Python

Computer Vision
└── OpenCV

ROS Image Processing
└── cv_bridge

Version Control
└── Git / GitHub
```

---

## 7. Run

### Gazebo

```bash
source /opt/ros/humble/setup.bash

export TURTLEBOT3_MODEL=waffle_pi

ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

### Build

```bash
cd ros2_ws

colcon build --symlink-install

source install/setup.bash
```

### Run Line Tracer Node

```bash
ros2 run line_tracer line_tracer_node
```

현재 단계에서는 카메라 영상에서 빨간색 라인을 검출하고
라인 중심 좌표 및 오차를 확인하는 단계까지 구현되어 있습니다.

---

## 8. Development History

### Prototype

먼저 OpenCV와 Windows 웹캠을 이용하여
빨간색 라인 검출 및 중심 오차 계산을 독립적으로 테스트했습니다.

```text
Webcam
  ↓
OpenCV
  ↓
HSV Red Detection
  ↓
Centroid
  ↓
Error
```

### ROS 2 Integration

이후 기존 OpenCV 알고리즘을 ROS 2 환경으로 확장하여
TurtleBot3 카메라 토픽과 연결했습니다.

```text
TurtleBot3 Camera
  ↓
ROS 2 Image Topic
  ↓
cv_bridge
  ↓
OpenCV
  ↓
Red Line Detection
```

현재는 이미지 처리 단계까지 완료했으며,
다음 단계에서 검출 결과를 `/cmd_vel`과 연결하여
실제 라인 트레이싱 제어를 구현할 예정입니다.

---

## 9. Project Objective

이 프로젝트를 통해 다음 기술을 직접 구현하고 검증하는 것을 목표로 합니다.

* ROS 2 Node / Topic 기반 통신
* `sensor_msgs/Image` 처리
* `cv_bridge`
* OpenCV 영상 처리
* HSV 기반 색상 검출
* Image Moment 기반 중심점 계산
* 오차 기반 제어
* ROS 2 `/cmd_vel` 제어
* TurtleBot3 Gazebo Simulation
* Git / GitHub 기반 프로젝트 관리

최종적으로 카메라 기반 비전 인식과 ROS 2 제어를 결합한
TurtleBot3 자율주행 시스템을 구현합니다.

```

