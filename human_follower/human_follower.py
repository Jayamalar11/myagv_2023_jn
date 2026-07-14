#!/usr/bin/env python3
import rospy
import cv2
import mediapipe as mp
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist

class MultiPersonFollower:
    def __init__(self):
        rospy.init_node('multi_person_follower', anonymous=True)
        self.bridge = CvBridge()
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
        
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            model_complexity=0, 
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        
        rospy.Subscriber("/camera/color/image_raw", Image, self.image_callback, queue_size=1, buff_size=2**24)
        rospy.loginfo("Adaptive Center-Alignment Follower Active.")

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        small_frame = cv2.resize(frame, (320, 240))
        rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        results = self.pose.process(rgb)
        twist = Twist()
        
        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            
            # Torso Center (X-axis)
            torso_x = (lm[11].x + lm[12].x + lm[23].x + lm[24].x) / 4
            
            # --- 1. ANGULAR ALIGNMENT (The Fix) ---
            # Center is 0.5. Calculate error.
            error_x = torso_x - 0.5 
            
            # DEADZONE: If error is less than 0.05, consider it "centered"
            if abs(error_x) < 0.05:
                twist.angular.z = 0.0
            else:
                # INCREASED GAIN: -2.5 makes it turn much faster to align
                twist.angular.z = -2.5 * error_x
            
            # --- 2. DISTANCE MAINTENANCE ---
            shoulder_width = abs(lm[11].x - lm[12].x) * 320
            
            if shoulder_width < 50:
                twist.linear.x = 0.2
            elif shoulder_width > 80:
                twist.linear.x = -0.2
            else:
                twist.linear.x = 0.0
            
            # Visual Debug: Draw center line and target line
            cv2.line(small_frame, (160, 0), (160, 240), (255, 0, 0), 1)
            cv2.line(small_frame, (int(torso_x*320), 0), (int(torso_x*320), 240), (0, 255, 0), 1)
        
        self.pub.publish(twist)
        cv2.imshow("Tracking View", small_frame)
        cv2.waitKey(1)

if __name__ == '__main__':
    try:
        MultiPersonFollower()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
