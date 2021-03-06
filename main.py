import math
from multiprocessing import Process

import cv2
import cvzone
import numpy as np
from cvzone.HandTrackingModule import HandDetector  # 手部检测方法
import pyautogui
import autopy
import psutil


def getDist_P2P(Point0, PointA):
    distance = math.pow((Point0[0] - PointA[0]), 2) + math.pow((Point0[1] - PointA[1]), 2)
    distance = math.sqrt(distance)
    return distance


class Detector:
    __CAN_DO = 0
    __CLICKED = 1
    __DOUBLE_CLICKED = 2
    __RIGHT_CLICKED = 3

    __previousMouseX = 0
    __previousMouseY = 0  # 上一帧时的鼠标所在位置
    __verticalMove = 30
    __horizontalMove = 30
    __canReClick = True
    __canReDoubleClick = True
    __canRightClick = True
    __canDo = 0  # 实现三种点击的互斥
    __clickThreshold = 1.15
    __doubleClickThreshold = 1.6
    __rightClickThreshold = 1.8
    __isMouseDown = False
    __smooth = 5  # 自定义平滑系数，让鼠标移动平缓一些
    __screenW = 10
    __screenH = 10
    __hands = None
    __detector = None
    p = None

    def __init__(self):
        self.p = Process(target=self.__detect())

    def __detect(self):
        self.__dealWithHandImage()

    def startDetect(self):
        self.p.start()

    def pause(self):
        ps = psutil.Process(pid=self.p.pid)
        ps.suspend()

    def reStart(self):
        ps = psutil.Process(pid=self.p.pid)
        ps.resume()

    def exit(self):
        ps = psutil.Process(pid=self.p.pid)
        ps.kill()

    def __detectMouse(self, image, pt1, pt2):

        lmList = self.__hands[0]['lmList']  # hands是由N个字典组成的列表，字典包每只手的关键点信息

        centerX, centerY = self.__hands[0]['center']
        cv2.circle(image, (centerX, centerY), 15, (255, 255, 0), cv2.FILLED)  # 颜色填充整个圆

        # 获取食指指尖坐标，和中指指尖坐标
        x1, y1, z1 = lmList[4]
        x2, y2, z2 = lmList[8]
        x3, y3, z3 = lmList[12]
        x5, y5, z5 = lmList[20]

        baseX1, baseY1, c = lmList[0]
        baseX2, baseY2, c1 = lmList[5]
        baseDistance = getDist_P2P((baseX1, baseY1), (baseX2, baseY2))  # 手掌根部到食指根部的距离

        # （5）检查哪个手指是朝上的
        fingers = self.__detector.fingersUp(self.__hands[0])

        # （6）确定鼠标移动的范围
        # 将食指的移动范围从预制的窗口范围，映射到电脑屏幕范围
        windowsX = np.interp(centerX, (pt1[0], pt2[0]), (0, self.__screenW))
        windowsY = np.interp(centerY, (pt1[1], pt2[1]), (0, self.__screenH))

        # （7）平滑，使手指在移动鼠标时，鼠标箭头不会一直晃动
        currentMouseX = self.__previousMouseX + (windowsX - self.__previousMouseX) / self.__smooth  # 当前的鼠标所在位置坐标
        currentMouseY = self.__previousMouseY + (windowsY - self.__previousMouseY) / self.__smooth
        # （8）移动鼠标
        autopy.mouse.move(currentMouseX / 2, currentMouseY / 2)

        # 更新前一帧的鼠标所在位置坐标，将当前帧鼠标所在位置，变成下一帧的鼠标前一帧所在位置
        self.__previousMouseX, self.__previousMouseY = currentMouseX, currentMouseY

        if fingers[1] == 1:  # 食指竖起，左键单击
            distance = getDist_P2P((x1, y1), (x2, y2))
            if distance / baseDistance > self.__clickThreshold:
                if self.__canDo == self.__CAN_DO:
                    pyautogui.click()
                    self.__canDo = self.__CLICKED
                if self.__canDo == 1:
                    cv2.circle(image, (x2, y2), 15, (0, 255, 0), cv2.FILLED)
            else:
                self.__canDo = self.__CAN_DO

        if fingers[2] == 1:  # 左键双击
            distance = getDist_P2P((x1, y1), (x3, y3))
            if distance / baseDistance > self.__doubleClickThreshold:
                if self.__canDo == self.__CAN_DO:
                    pyautogui.doubleClick()
                    self.__canDo = self.__DOUBLE_CLICKED
                if self.__canDo == self.__DOUBLE_CLICKED:
                    cv2.circle(image, (x3, y3), 15, (0, 255, 0), cv2.FILLED)
            else:
                self.__canDo = self.__CAN_DO

        if fingers[4] == 1:  # 右键
            distance = getDist_P2P((x1, y1), (x5, y5))
            if distance / baseDistance > self.__rightClickThreshold:
                if self.__canDo == self.__CAN_DO:
                    pyautogui.rightClick()
                    self.__canDo = self.__RIGHT_CLICKED
                if self.__canDo == self.__RIGHT_CLICKED:
                    cv2.circle(image, (x5, y5), 15, (0, 255, 0), cv2.FILLED)
            else:
                self.__canDo = self.__CAN_DO

        if fingers == [0, 0, 1, 1, 1]:  # 比3动作,上滑
            self.__detectScroll(isVertical=True, isUp=True)

        if fingers == [0, 0, 0, 1, 1]:  # 比2，下滑
            self.__detectScroll(isVertical=True, isUp=False)

    def __detectScroll(self, isVertical, isUp):
        if isVertical:
            if isUp:
                pyautogui.vscroll(self.__verticalMove)
            else:
                pyautogui.vscroll(-self.__verticalMove)

    def __dealWithHandImage(self):
        fpsReader = cvzone.FPS()
        # （1）导数视频数据
        self.__screenW, self.__screenH = pyautogui.size()  # 返回电脑屏幕的宽和高(2160,1440)
        cameraW, cameraH = (1280, 720)  # 视频显示窗口的宽和高
        pt1, pt2 = (100, 100), (1180, 620)  # 虚拟鼠标的移动范围，左上坐标pt1，右下坐标pt2

        cap = cv2.VideoCapture(0)  # 0代表自己电脑的摄像头
        cap.set(3, cameraW)  # 设置显示框的宽度1280
        cap.set(4, cameraH)  # 设置显示框的高度720

        # （2）接收手部检测方法
        self.__detector = HandDetector(mode=False,  # 视频流图像
                                       maxHands=1,  # 最多检测一只手
                                       detectionCon=0.8,  # 最小检测置信度
                                       minTrackCon=0.5)  # 最小跟踪置信度

        # （3）处理每一帧图像
        while True:
            # 图片是否成功接收、img帧图像
            success, img = cap.read()

            # 翻转图像，使自身和摄像头中的自己呈镜像关系
            img = cv2.flip(img, flipCode=1)  # 1代表水平翻转，0代表竖直翻转

            # 在图像窗口上创建一个矩形框，在该区域内移动鼠标
            cv2.rectangle(img, pt1, pt2, (0, 255, 255), 3)

            # （4）手部关键点检测
            # 传入每帧图像, 返回手部关键点的坐标信息(字典)，绘制关键点后的图像
            self.__hands, img = self.__detector.findHands(img, flipType=False)  # 上面反转过了，这里就不用再翻转了

            # 如果能检测到手那么就进行下一步
            if self.__hands:
                self.__detectMouse(image=img, pt1=pt1, pt2=pt2)

            # （10）显示图像
            # 查看FPS
            fps, img = fpsReader.update(img, pos=(20, 40), color=(0, 255, 0), scale=2, thickness=3)
            # 显示图像，输入窗口名及图像数据
            cv2.imshow('image', img)
            if cv2.waitKey(1) & 0xFF == 27:  # 每帧滞留20毫秒后消失，ESC键退出
                break

        # 释放视频资源
        cap.release()
        cv2.destroyAllWindows()
