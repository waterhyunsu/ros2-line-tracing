import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge

import cv2
import numpy as np


class LineTracerNode(Node):

    def __init__(self):
        super().__init__('line_tracer_node')

        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.get_logger().info('Line Tracer Node started')
        self.get_logger().info('Waiting for camera image...')

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )

        # BGR -> HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Red color detection
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])

        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])

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

        # Calculate image moments
        moments = cv2.moments(red_mask)

        if moments['m00'] > 0:

            # Red line center
            cx = int(moments['m10'] / moments['m00'])
            cy = int(moments['m01'] / moments['m00'])

            cv2.circle(
                frame,
                (cx, cy),
                5,
                (0, 255, 0),
                -1
            )

            # Image center
            image_center_x = frame.shape[1] // 2

            # Error
            error = cx - image_center_x

            # P controller
            KP = 0.005

            angular_z = -KP * error

            # Limit angular velocity
            angular_z = max(
                -1.0,
                min(1.0, angular_z)
            )

            # Speed control based on error
            if abs(error) <= 30:
                linear_x = 0.10
            elif abs(error) <= 80:
                linear_x = 0.07
            else:
                linear_x = 0.05

            # Publish velocity command
            cmd = Twist()

            cmd.linear.x = linear_x
            cmd.angular.z = angular_z

            self.cmd_vel_publisher.publish(cmd)

            # Draw image center
            cv2.line(
                frame,
                (image_center_x, 0),
                (image_center_x, frame.shape[0]),
                (255, 0, 0),
                2
            )

            # Display control values
            cv2.putText(
                frame,
                f'CX: {cx}  Error: {error}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f'Linear: {linear_x:.2f}  Angular: {angular_z:.3f}',
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        else:

            # Stop when red line is not detected
            cmd = Twist()

            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

            self.cmd_vel_publisher.publish(cmd)

            cv2.putText(
                frame,
                'RED LINE NOT FOUND',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        cv2.imshow(
            'Red Line Detection',
            frame
        )

        cv2.imshow(
            'Red Mask',
            red_mask
        )

        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)

    node = LineTracerNode()

    rclpy.spin(node)

    node.destroy_node()

    cv2.destroyAllWindows()

    rclpy.shutdown()


if __name__ == '__main__':
    main()