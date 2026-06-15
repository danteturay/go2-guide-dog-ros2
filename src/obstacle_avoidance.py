import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

# Minimum safe distance in metres before the robot stops
SAFE_DISTANCE = 1.0

class ObstacleAvoidanceNode(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')
        
        # Subscribe to LiDAR scan data
        self.scan_subscriber = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        # Subscribe to raw velocity commands from user/planner
        self.cmd_subscriber = self.create_subscription(
            Twist,
            '/cmd_vel_raw',
            self.cmd_callback,
            10
        )
        
        # Publish safe velocity commands to robot
        self.cmd_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )
        
        self.latest_cmd = Twist()  # store latest command
        self.obstacle_detected = False
        
        self.get_logger().info('Obstacle avoidance node started')

    def scan_callback(self, msg):
        # Get the minimum distance reading from the LiDAR
        # Filter out invalid readings (0.0 or inf)
        valid_ranges = [r for r in msg.ranges if 0.1 < r < float('inf')]
        
        if not valid_ranges:
            return
            
        min_distance = min(valid_ranges)
        
        if min_distance < SAFE_DISTANCE:
            self.obstacle_detected = True
            self.get_logger().warn(
                f'Obstacle detected at {min_distance:.2f}m - stopping robot'
            )
            # Publish stop command
            self.cmd_publisher.publish(Twist())
        else:
            self.obstacle_detected = False
            # Safe to move - forward latest command
            self.cmd_publisher.publish(self.latest_cmd)

    def cmd_callback(self, msg):
        # Store the latest movement command
        self.latest_cmd = msg
        
        # If no obstacle, forward it immediately
        if not self.obstacle_detected:
            self.cmd_publisher.publish(msg)

def main():
    rclpy.init()
    node = ObstacleAvoidanceNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()