#!/usr/bin/env python3
import rclpy, yaml, os, math
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import PoseWithCovarianceStamped

WAYPOINT_FILE = os.path.expanduser(
    '~/myagv_ros2/src/myagv_navigation2/config/waypoints.yaml')

def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                       1.0 - 2.0 * (q.y * q.y + q.z * q.z))

class WaypointRecorder(Node):
    def __init__(self):
        super().__init__('waypoint_recorder')
        self.sub = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.callback, 10)
        self.recording = False

    def callback(self, msg):
        # Prevent multiple triggers from back-to-back AMCL messages
        if self.recording:
            return
        self.recording = True
        
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        yaw = yaw_from_quaternion(msg.pose.pose.orientation)
        
        # This will block, but MultiThreadedExecutor keeps the background alive
        name = input("\n[AMCL Pose Received] Name this location: ").strip()
        if not name:
            name = f"waypoint_{int(x)}_{int(y)}"
            
        data = {}
        
        # Ensure the destination folder exists before saving
        os.makedirs(os.path.dirname(WAYPOINT_FILE), exist_ok=True)
        
        if os.path.exists(WAYPOINT_FILE):
            with open(WAYPOINT_FILE) as f:
                data = yaml.safe_load(f) or {}
                
        data[name] = {'x': round(x, 3), 'y': round(y, 3), 'yaw': round(yaw, 3)}
        
        with open(WAYPOINT_FILE, 'w') as f:
            yaml.dump(data, f)
            
        print(f"✅ Saved '{name}' at x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}\n")
        
        # Signal executor to stop
        rclpy.get_default_context().on_shutdown(lambda: None)
        self.get_node_options()
        os._exit(0) # Immediate clean exit from python thread

def main():
    rclpy.init()
    node = WaypointRecorder()
    # Use MultiThreadedExecutor so input() doesn't freeze ROS
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
