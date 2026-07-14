#!/usr/bin/env python3
import sys, yaml, os, math
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

WAYPOINT_FILE = os.path.expanduser(
    '~/myagv_ros2/src/myagv_navigation2/config/waypoints.yaml')

def make_pose(navigator, x, y, yaw):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 goto_waypoint.py <location_name>")
        return
    name = sys.argv[1]
    with open(WAYPOINT_FILE) as f:
        waypoints = yaml.safe_load(f)
    if not waypoints or name not in waypoints:
        print(f"Unknown location '{name}'. Options: {list((waypoints or {}).keys())}")
        return

    rclpy.init()
    navigator = BasicNavigator()
    navigator.waitUntilNav2Active()

    wp = waypoints[name]
    goal = make_pose(navigator, wp['x'], wp['y'], wp['yaw'])
    print(f"Heading to '{name}'...")
    navigator.goToPose(goal)
    while not navigator.isTaskComplete():
        pass

    result = navigator.getResult()
    print("Arrived!" if result == TaskResult.SUCCEEDED else f"Failed: {result}")

if __name__ == '__main__':
    main()
