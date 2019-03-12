#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pygame
import sys
import rospy
import tf
import math
import subprocess
from pygame.locals import FULLSCREEN, QUIT, KEYDOWN, K_ESCAPE
from geometry_msgs.msg import QuaternionStamped, Quaternion

class RosEyes(object):
    def __init__(self):
        self._quaternion = QuaternionStamped()
        self._quaternion.quaternion.x = 0.0
        self._quaternion.quaternion.y = 0.0
        self._quaternion.quaternion.z = 0.0
        self._quaternion.quaternion.w = 1.0
        bg_color_str = rospy.get_param('~bg_color', "255,255,255")
        self.bg_color_set = list()
        for item in bg_color_str.split(","):
            self.bg_color_set.append(int(item))
        self.hz = rospy.get_param('~hz', 30)
        rospy.Subscriber("src_topic", QuaternionStamped, self.quaternion_callback)
        # pygame
        pygame.init()
        if rospy.get_param('~is_fullscreen', "false"):
            cmd1 = ['xrandr']
            cmd2 = ['grep', '*']
            resolution_string, _ = self._command2pipe(cmd1, cmd2)
            resolution = resolution_string.split()[0]
            width, height = resolution.split('x')
            self.screen_size = (int(width), int(height))
            self.screen = pygame.display.set_mode(self.screen_size, FULLSCREEN, 32)
        else:
            self.screen_size = (rospy.get_param('~width', 800), rospy.get_param('~height', 480))
            self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("roseyes")
        # pygame
        self.update_loop()

    def quaternion_callback(self, message):
        self._quaternion = message

    def update_loop(self):
        r = rospy.Rate(self.hz)
        while not rospy.is_shutdown():
            self.screen.fill(self.bg_color_set)
            # left
            pygame.draw.ellipse(self.screen, (0,0,0), (0,0,self.screen_size[0]/2,self.screen_size[1]), 5)
            # right
            pygame.draw.ellipse(self.screen, (0,0,0), (self.screen_size[0]/2,0,self.screen_size[0]/2,self.screen_size[1]), 5)
            # x -> z
            # y -> y
            euler = tf.transformations.euler_from_quaternion((self._quaternion.quaternion.x, self._quaternion.quaternion.y, self._quaternion.quaternion.z, self._quaternion.quaternion.w))
            euler_org_x = 0.0
            euler_org_y = euler[1]
            if euler[0] <= 0:
                if euler_org_y >= 0:
                    euler_org_z = euler[2] - euler[0]
                else:
                    euler_org_z = euler[2] + euler[0]
            else:
                if euler_org_y >= 0:
                    euler_org_z = euler[2] - euler[0]
                else:
                    euler_org_z = euler[2] - euler[0]

            left_eye_center_x = self.screen_size[0] / 2 / 2
            left_eye_center_y = self.screen_size[1] / 2
            # transform euler x=0
            x_org = self._calclate_quaternion_to_display_positon(euler_org_z, left_eye_center_x, True)
            y_org = self._calclate_quaternion_to_display_positon(euler_org_y, left_eye_center_y, False)
            rospy.logdebug("euler" + str(euler))
            rospy.logdebug("new euler" + str((euler_org_x, euler_org_y, euler_org_z)))
            rospy.logdebug("org" + str((x_org, y_org)))
            eye_x = 0.0
            eye_y = 0.0
            if (x_org - left_eye_center_x) == 0.0:
                eye_x = x_org
                eye_y = y_org
            else:
                # line 
                l_c = (y_org - left_eye_center_y) / (x_org - left_eye_center_x)
                l_d = left_eye_center_y - l_c * left_eye_center_x
                
                # ellipse
                e_a = (1.0 / ((left_eye_center_x) ** 2) + ((l_c ** 2) / (left_eye_center_y ** 2)))
                e_b = ((-2.0 * left_eye_center_x) / (left_eye_center_x ** 2)) + ((2.0 * l_c * (l_d - left_eye_center_y)) / (left_eye_center_y ** 2))
                e_c = (left_eye_center_x ** 2 / left_eye_center_x ** 2) + (((l_d - left_eye_center_y) ** 2) / (left_eye_center_y ** 2) -1)
                e_d = (e_b ** 2) - (4 * e_a * e_c)
                if e_d > 0:
                    result_plus_x = (-1 * e_b + math.sqrt(e_d)) / (2 * e_a)
                    result_plus_y = l_c * result_plus_x + l_d
                    result_minus_x = (-1 * e_b - math.sqrt(e_d)) / (2 * e_a)
                    result_minus_y = l_c * result_minus_x + l_d
                    rospy.logdebug(result_plus_x, result_plus_y, result_minus_x, result_minus_y) 
                    distance_plus = math.sqrt(((result_plus_x - x_org) ** 2) + ((result_plus_y - y_org) ** 2))
                    distance_minus = math.sqrt(((result_minus_x - x_org) ** 2) + ((result_minus_y - y_org) ** 2))
                    rospy.logdebug("dist" + str((distance_plus, distance_minus))) 
                    if distance_plus <= distance_minus:
                        if x_org <= left_eye_center_x:
                            if x_org <= result_plus_x:
                                eye_x = result_plus_x
                            else:
                                eye_x = x_org
                        else:
                            if x_org <= result_plus_x:
                                eye_x = x_org
                            else:
                                eye_x = result_plus_x
                        if y_org <= left_eye_center_y:
                            if y_org <= result_plus_y:
                                eye_y = result_plus_y
                            else:
                                eye_y = y_org
                        else:
                            if y_org <= result_plus_y:
                                eye_y = y_org
                            else:
                                eye_y = result_plus_y
                    else:
                        if x_org <= left_eye_center_x:
                            if x_org <= result_minus_x:
                                eye_x = result_minus_x
                            else:
                                eye_x = x_org
                        else:
                            if x_org <= result_minus_x:
                                eye_x = x_org
                            else:
                                eye_x = result_minus_x
                        if y_org <= left_eye_center_y:
                            if y_org <= result_minus_y:
                                eye_y = result_minus_y
                            else:
                                eye_y = y_org
                        else:
                            if y_org <= result_minus_y:
                                eye_y = y_org
                            else:
                                eye_y = result_minus_y
                elif e_d == 0:
                    eye_x = -1 * e_b / (2 * e_a)
                    eye_y = l_c * eye_x + l_d
                else:
                    eye_x = x_org
                    eye_y = y_org
            if left_eye_center_y - eye_y >= 0:
                eye_y = left_eye_center_y + (left_eye_center_y - eye_y)
            else:
                eye_y = left_eye_center_y - (eye_y - left_eye_center_y)
            if left_eye_center_x - eye_x >= 0:
                eye_x = left_eye_center_x + (left_eye_center_x - eye_x)
            else:
                eye_x = left_eye_center_x - (eye_x - left_eye_center_x)
            rospy.loginfo("result" + str((eye_x, eye_y))) 
            # left
            pygame.draw.circle(self.screen, (0,0,0), (int(eye_x), int(eye_y)), 25)
            # right
            pygame.draw.circle(self.screen, (0,0,0), (int(eye_x + left_eye_center_x * 2), int(eye_y)), 25)

            pygame.display.update()
            for event in pygame.event.get():
                if event.type == QUIT:
                    rospy.signal_shutdown("close button")
                    return
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        rospy.signal_shutdown("close button")
                        return
            r.sleep()

    def _calclate_quaternion_to_display_positon(self, euler, left_eye_center, x_flags):
        org = 0.0
        if abs(euler / (math.pi / 2)) <= 1.0:
            org = (euler / (math.pi / 2.0) * left_eye_center) + left_eye_center
        else:
            if euler >= 0:
                org = left_eye_center * 2.0
            else:
                if x_flags == True:
                    org = 0
                else:
                    org = left_eye_center * 2.0
        return org

    def _command2pipe(self, cmd1, cmd2):
        p = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE)
        p.stdout.close()
        first_line, rest_lines = p2.communicate()
        return(first_line, rest_lines)


def main():
    rospy.init_node('ros_eyes', anonymous=True)
    RosEyes()
    rospy.spin()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        print "program interrupted before completion"

