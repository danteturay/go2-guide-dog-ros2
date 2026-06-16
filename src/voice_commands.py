import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import threading
import speech_recognition as sr

# Keyword to velocity mapping
COMMANDS = {
    # Forward
    'forward':      (0.5, 0.0),
    'go forward':   (0.5, 0.0),
    'move forward': (0.5, 0.0),
    'ahead':        (0.5, 0.0),
    'go ahead':     (0.5, 0.0),
    'slowly':       (0.2, 0.0),
    'go slowly':    (0.2, 0.0),
    'slow down':    (0.2, 0.0),
    # Stop
    'stop':         (0.0, 0.0),
    'halt':         (0.0, 0.0),
    'freeze':       (0.0, 0.0),
    'wait':         (0.0, 0.0),
    # Backward
    'back':         (-0.3, 0.0),
    'go back':      (-0.3, 0.0),
    'backward':     (-0.3, 0.0),
    'reverse':      (-0.3, 0.0),
    # Turn left
    'left':         (0.0, 0.5),
    'turn left':    (0.0, 0.5),
    'go left':      (0.0, 0.5),
    # Turn right
    'right':        (0.0, -0.5),
    'turn right':   (0.0, -0.5),
    'go right':     (0.0, -0.5),
    # Speed up/down
    'faster':       (0.8, 0.0),
    'speed up':     (0.8, 0.0),
}

class VoiceCommandNode(Node):
    def __init__(self):
        super().__init__('voice_commands')

        self.cmd_publisher = self.create_publisher(Twist, '/cmd_vel_raw', 10)
        self.text_publisher = self.create_publisher(String, '/voice_text', 10)

        self.recognizer = sr.Recognizer()
        self.get_logger().info('Voice command node started - listening...')

        self.listen_thread = threading.Thread(target=self.listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def listen_loop(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.get_logger().info('Microphone ready - speak a command')

            while rclpy.ok():
                try:
                    self.get_logger().info('Listening...')
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio).lower()
                    self.get_logger().info(f'Heard: {text}')

                    # Publish recognised text
                    msg = String()
                    msg.data = text
                    self.text_publisher.publish(msg)

                    # Match command
                    self.process_command(text)

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    self.get_logger().info('Could not understand audio')
                except Exception as e:
                    self.get_logger().warn(f'Error: {e}')

    def process_command(self, text):
        # Check for keyword matches (longest match first)
        matched = None
        matched_key = ''

        for keyword, velocities in COMMANDS.items():
            if keyword in text and len(keyword) > len(matched_key):
                matched = velocities
                matched_key = keyword

        if matched:
            linear_x, angular_z = matched
            cmd = Twist()
            cmd.linear.x = linear_x
            cmd.angular.z = angular_z
            self.cmd_publisher.publish(cmd)
            self.get_logger().info(
                f'Command: "{matched_key}" -> linear_x={linear_x}, angular_z={angular_z}'
            )
        else:
            self.get_logger().warn(f'Unknown command: "{text}"')

def main():
    rclpy.init()
    node = VoiceCommandNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()