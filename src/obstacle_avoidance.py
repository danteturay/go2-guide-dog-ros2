import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import struct

# Distance thresholds
STOP_DISTANCE = 1      # Stop completely within 0.8m
SLOW_DISTANCE = 2.0      # Slow down within 2.0m
SLOW_SPEED_FACTOR = 0.3  # Reduce speed to 30% when slowing

# Only consider points in front of the robot and at relevant heights
MIN_HEIGHT = -0.1        # Ignore ground
MAX_HEIGHT = 1.5         # Ignore things above robot
FRONT_ANGLE = 60         # Degrees either side of forward direction

class ObstacleAvoidanceNode(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        # Subscribe to PointCloud2 LiDAR data
        self.scan_subscriber = self.create_subscription(
            PointCloud2,
            '/velodyne_points',
            self.pointcloud_callback,
            10
        )

        # Subscribe to raw velocity commands
        self.cmd_subscriber = self.create_subscription(
            Twist,
            '/cmd_vel_raw',
            self.cmd_callback,
            10
        )

        # Subscribe to YOLO detections
        self.detection_subscriber = self.create_subscription(
            String,
            '/detections',
            self.detection_callback,
            10
        )

        # Publish safe velocity commands
        self.cmd_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Publish status for voice feedback
        self.status_publisher = self.create_publisher(String, '/robot_status', 10)

        self.latest_cmd = Twist()
        self.min_distance = float('inf')
        self.latest_detection = None

        self.get_logger().info('Obstacle avoidance node started (PointCloud2)')

    def detection_callback(self, msg):
        self.latest_detection = msg.data

    def pointcloud_callback(self, msg):
        # Parse PointCloud2 message to find minimum distance to obstacles
        # PointCloud2 data is packed binary - we need to unpack x, y, z
        
        point_step = msg.point_step  # bytes per point
        data = msg.data

        min_dist = float('inf')

        # Read each point
        for i in range(msg.width * msg.height):
            offset = i * point_step
            
            try:
                # Unpack x, y, z as floats (4 bytes each)
                x = struct.unpack_from('f', data, offset)[0]
                y = struct.unpack_from('f', data, offset + 4)[0]
                z = struct.unpack_from('f', data, offset + 8)[0]
            except struct.error:
                continue

            # Filter out invalid points
            if not all(map(lambda v: -100 < v < 100, [x, y, z])):
                continue

            # Filter by height — ignore ground and things above robot
            if z < MIN_HEIGHT or z > MAX_HEIGHT:
                continue

            # Only consider points in front of robot
            # x is forward, y is sideways
            import math
            angle = math.degrees(math.atan2(y, x))
            if abs(angle) > FRONT_ANGLE:
                continue

            # Calculate horizontal distance
            dist = math.sqrt(x**2 + y**2)
            if dist < min_dist:
                min_dist = dist

        self.min_distance = min_dist
        self.apply_safety(self.latest_cmd)

    def cmd_callback(self, msg):
        self.latest_cmd = msg
        self.apply_safety(msg)

    def apply_safety(self, cmd):
        safe_cmd = Twist()
        status = String()

        if self.min_distance < STOP_DISTANCE:
            status.data = f'STOP: obstacle at {self.min_distance:.2f}m'
            if self.latest_detection:
                status.data += f' ({self.latest_detection})'
            self.get_logger().warn(status.data)

        elif self.min_distance < SLOW_DISTANCE:
            safe_cmd.linear.x = cmd.linear.x * SLOW_SPEED_FACTOR
            safe_cmd.angular.z = cmd.angular.z
            status.data = f'SLOW: obstacle at {self.min_distance:.2f}m'
            if self.latest_detection:
                status.data += f' ({self.latest_detection})'
            self.get_logger().info(status.data)

        else:
            safe_cmd = cmd
            status.data = 'CLEAR'

        self.cmd_publisher.publish(safe_cmd)
        self.status_publisher.publish(status)

def main():
    rclpy.init()
    node = ObstacleAvoidanceNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
