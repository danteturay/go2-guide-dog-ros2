import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import threading

class VoiceFeedbackNode(Node):
    def __init__(self):
        super().__init__('voice_feedback')

        self.status_subscriber = self.create_subscription(
            String,
            '/robot_status',
            self.status_callback,
            10
        )

        self.last_spoken_type = ''
        self.get_logger().info('Voice feedback node started')

    def status_callback(self, msg):
        status = msg.data
        status_type = status.split(':')[0].strip()

        if status_type == self.last_spoken_type:
            return

        self.last_spoken_type = status_type

        if status_type == 'STOP':
            text = 'Warning, obstacle detected. Stopping.'
            if '(' in status:
                obj = status.split('(')[1].split(')')[0]
                text = f'Warning, {obj} detected ahead. Stopping.'
        elif status_type == 'SLOW':
            text = 'Obstacle nearby, slowing down.'
        else:
            text = ''

        if text:
            self.get_logger().info(f'Speaking: {text}')
            self.speak(text)

    def speak(self, text):
        def _speak():
            try:
                subprocess.run(['espeak', text], capture_output=True, timeout=5)
            except Exception as e:
                self.get_logger().warn(f'Speech failed: {e}')

        thread = threading.Thread(target=_speak)
        thread.daemon = True
        thread.start()

def main():
    rclpy.init()
    node = VoiceFeedbackNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
