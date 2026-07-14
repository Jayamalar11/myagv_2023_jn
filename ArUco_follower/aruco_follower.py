#!/usr/bin/env python3
import rospy
import cv2
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist

class RobotController:
    def __init__(self):
        # 1. Initialize ROS Node
        rospy.init_node('agv_follower', anonymous=True)
        self.bridge = CvBridge()
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
        
        # 2. ArUco Detector Configuration (4x4 Matrix)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters()
        
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 23
        self.aruco_params.adaptiveThreshWinSizeStep = 10
        self.aruco_params.adaptiveThreshConstant = 7
        self.aruco_params.perspectiveRemovePixelPerCell = 4
        self.aruco_params.perspectiveRemoveIgnoredMarginPerCell = 0.13
        self.aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
        # 3. Anti-Stutter Memory Variables
        self.last_seen_time = rospy.get_time()
        self.last_twist = Twist()
        self.COAST_TIME = 0.5 
        
        rospy.Subscriber("/camera/color/image_raw", Image, self.image_callback)
        rospy.loginfo("Smoothed ArUco Follower initialized. Adjusted for gentler turning.")

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        twist = Twist()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)
        
        aruco_found = False
        marker_width = 0
        current_time = rospy.get_time()
        
        if ids is not None:
            aruco_found = True
            self.last_seen_time = current_time 
            marker_corners = corners[0][0]
            
            # --- 1. Smoothed Dynamic Turning ---
            center_x = np.mean(marker_corners[:, 0])
            error_x = center_x - 320 
            
            # Reduced multiplier for gentler panning
            raw_turn = -0.003 * error_x 
            
            # Reduced Clamp: Caps the maximum spin speed to a moderate pace
            twist.angular.z = max(-0.6, min(0.6, raw_turn))
            
            # --- 2. Range Maintenance ---
            marker_width = marker_corners[1][0] - marker_corners[0][0]
            
            if marker_width < 190:
                twist.linear.x = 0.20  
            elif marker_width > 210:
                twist.linear.x = -0.20 
            else:
                twist.linear.x = 0.0   
                
            self.last_twist = twist
            cv2.aruco.drawDetectedMarkers(frame, corners)
            
        else:
            # --- 3. The Grace Period (Anti-Stutter) ---
            time_since_last_seen = current_time - self.last_seen_time
            
            if time_since_last_seen < self.COAST_TIME:
                twist = self.last_twist
            else:
                twist.linear.x = 0.0
                twist.angular.z = 0.0
                self.last_twist = Twist() 
            
        self.pub.publish(twist)
        
        # --- 4. UI Display ---
        if aruco_found:
            cv2.putText(frame, "TRACKING ACTIVE", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        elif (current_time - self.last_seen_time) < self.COAST_TIME:
            cv2.putText(frame, "COASTING (BLUR)", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        else:
            cv2.putText(frame, "TARGET LOST - STOPPED", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        cv2.drawMarker(frame, (320, 240), (0, 255, 255), cv2.MARKER_CROSS, 20, 2)
        cv2.imshow("Jetson Feed", frame)
        cv2.waitKey(1)

if __name__ == '__main__':
    try:
        RobotController()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
