import math

import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector  # 手部检测方法
import cvzone
import pyautogui
import autopy

previousMouseX = 0
previousMouseY = 0  # 上一帧时的鼠标所在位置
verticalMove = 30
horizontalMove = 30
canReClick = True
canReDoubleClick = True
canRightClick = True
canDo = 0  # 实现三种点击的互斥
clickThreshold = 1.15
doubleClickThreshold = 1.6
rightClickThreshold = 1.8

def detectMouse(img):
    global previousMouseY
    global previousMouseX
    global canReClick
    global canReDoubleClick
    global canRightClick
    global canDo
    global clickThreshold
    global doubleClickThreshold
    global rightClickThreshold

    lmList = hands[0]['lmList']  # hands是由N个字典组成的列表，字典包每只手的关键点信息

    centerX, centerY = hands[0]['center']
    cv2.circle(img, (centerX, centerY), 15, (255, 255, 0), cv2.FILLED)  # 颜色填充整个圆

    # 获取食指指尖坐标，和中指指尖坐标
    x1, y1, z1 = lmList[4]
    x2, y2, z2 = lmList[8]
    x3, y3, z3 = lmList[12]
    x5, y5, z5 = lmList[20]

    baseX1, baseY1, c = lmList[0]
    baseX2, baseY2, c1 = lmList[5]
    baseDistance = getDist_P2P((baseX1, baseY1), (baseX2, baseY2)) #手掌根部到食指根部的距离

    # （5）检查哪个手指是朝上的
    fingers = detector.fingersUp(hands[0])

    # （6）确定鼠标移动的范围
    # 将食指的移动范围从预制的窗口范围，映射到电脑屏幕范围
    windowsX = np.interp(centerX, (pt1[0], pt2[0]), (0, screenW))
    windowsY = np.interp(centerY, (pt1[1], pt2[1]), (0, screenH))

    # （7）平滑，使手指在移动鼠标时，鼠标箭头不会一直晃动
    currentMouseX = previousMouseX + (windowsX - previousMouseX) / smooth  # 当前的鼠标所在位置坐标
    currentMouseY = previousMouseY + (windowsY - previousMouseY) / smooth
    # （8）移动鼠标
    autopy.mouse.move(currentMouseX/2, currentMouseY/2)
    # pyautogui.moveTo(currentMouseX, currentMouseY)

    # 更新前一帧的鼠标所在位置坐标，将当前帧鼠标所在位置，变成下一帧的鼠标前一帧所在位置
    previousMouseX, previousMouseY = currentMouseX, currentMouseY

    if fingers[1] == 1:  # 食指竖起
        # distance, info, img = detector.findDistance((x1, y1), (x2, y2), img)
        distance = getDist_P2P((x1, y1), (x2, y2))
        if distance/baseDistance > clickThreshold:
            if canReClick and canDo == 0:
                pyautogui.click()
                canReClick = False
                canDo = 1
            if canDo == 1:
                cv2.circle(img, (x2, y2), 15, (0, 255, 0), cv2.FILLED)
        else:
            canReClick = True
            canDo = 0

    if fingers[2] == 1:
        # distance, info, img = detector.findDistance((x1, y1), (x3, y3), img)
        distance = getDist_P2P((x1, y1), (x3, y3))
        if distance/baseDistance > doubleClickThreshold:
            if canReDoubleClick and canDo == 0:
                pyautogui.doubleClick()
                canReDoubleClick = False
                canDo = 2
            if canDo == 2:
                cv2.circle(img, (x3, y3), 15, (0, 255, 0), cv2.FILLED)
        else:
            canReDoubleClick = True
            canDo = 0

    if fingers[4] == 1:
        # distance, info, img = detector.findDistance((x1, y1), (x5, y5), img)
        distance = getDist_P2P((x1, y1), (x5, y5))
        if distance/baseDistance > rightClickThreshold:
            if canRightClick and canDo == 0:
                pyautogui.rightClick()
                canRightClick = False
                canDo = 3
            if canDo == 3:
                cv2.circle(img, (x5, y5), 15, (0, 255, 0), cv2.FILLED)
        else:
            canRightClick = True
            canDo = 0

    if fingers == [0, 0, 1, 0, 0]:  # 竖中指
        detectScroll(isVertical=True, isUp=True)

    if fingers == [0, 0, 0, 1, 0]:  # 竖无名指
        detectScroll(isVertical=True, isUp=False)


def detectScroll(isVertical, isUp):
    if isVertical:
        if isUp:
            pyautogui.vscroll(verticalMove)
        else:
            pyautogui.vscroll(-verticalMove)


# ***** 求两点间距离*****
def getDist_P2P(Point0, PointA):
    distance = math.pow((Point0[0] - PointA[0]), 2) + math.pow((Point0[1] - PointA[1]), 2)
    distance = math.sqrt(distance)
    return distance


if __name__ == '__main__':
    fpsReader = cvzone.FPS()
    # （1）导数视频数据
    screenW, screenH = pyautogui.size()  # 返回电脑屏幕的宽和高(2160,1440)
    cameraW, cameraH = (1280, 720)  # 视频显示窗口的宽和高
    pt1, pt2 = (100, 100), (1180, 620)  # 虚拟鼠标的移动范围，左上坐标pt1，右下坐标pt2

    cap = cv2.VideoCapture(0)  # 0代表自己电脑的摄像头
    cap.set(3, cameraW)  # 设置显示框的宽度1280
    cap.set(4, cameraH)  # 设置显示框的高度720

    smooth = 5  # 自定义平滑系数，让鼠标移动平缓一些

    # （2）接收手部检测方法
    detector = HandDetector(mode=False,  # 视频流图像
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
        hands, img = detector.findHands(img, flipType=False)  # 上面反转过了，这里就不用再翻转了

        # 如果能检测到手那么就进行下一步
        if hands:
            detectMouse(img=img)

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
