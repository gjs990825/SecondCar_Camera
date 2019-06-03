import sensor
import image
import time
import lcd
from pyb import UART, Timer, LED

# 数据包字节标识
Pack_Header1 = 0
Pack_Header2 = 1
Pack_MainCmd = 2
Pack_SubCmd1 = 3
Pack_SubCmd2 = 4
Pack_SubCmd3 = 4
Pack_CheckSum = 6
Pack_Ending = 7

# 功能区分字节
OpenMV_Trafficlight = 0x01
OpenMV_Circle = 0x02
OpenMV_Rectangle = 0x03
OpenMV_ColorNumber = 0x04
OpenMV_AllColorNumber = 0x05


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  # 320*240
sensor.set_auto_exposure(False)    # 关闭自动白平衡
sensor.skip_frames(10)  # 刷新设置
# Initialize the lcd screen.
lcd.init()
# 创建串口对象
uart = UART(3, 115200, 8, None, 1)


# LED对象创建
LED_Red = LED(1)
LED_Green = LED(2)
LED_Blue = LED(3)

# 颜色阈值设定
red_traffic = (40, 72, 52, 81, -7, 60)
yellow_traffic = (51, 74, -11, 50, -14, 63)
green_traffic = (49, 84, -92, -44, -6, 57)

# 图形颜色阈值设定
red = (29, 71, 29, 80, 20, 67)
green = (29, 60, -62, -16, 4, 61)
blue = (9, 52, -6, 52, -77, -26)
yellow = (59, 94, -35, 15, 40, 94)
purple = (42, 76, 57, 101, -37, 26)
cyan = (47, 94, -69, -8, -47, -3)
black = (0, 45, -24, 19, -18, 25)
# 图形颜色阈值列表
color_list = [red, green, blue]

# 串口发送函数


def UART_Send(src, length):
    for i in range(length):
        uart.writechar(src[i])


# 置零list所有成员
def Reset_List(src):
    for i in range(len(src)):
        src[i] = 0


# 矩形识别
def Rect_Discern(index):
    sensor.set_framesize(sensor.QQVGA)
    img = sensor.snapshot().lens_corr(1.8)
    n = 0
    for c in img.find_rects(threshold=28000):
        area = (c.x(), c.y(), c.w(), c.h())
        statistics = img.get_statistics(roi=area)  # 像素颜色统计
        if(index > 0 and index <= len(color_list)):
            ranges = color_list[index - 1]
            if ranges[0] < statistics.l_mode() < ranges[1] and ranges[2] < statistics.a_mode() < ranges[3] and ranges[4] < statistics.b_mode() < ranges[5]:
                n = n + 1
        else:
            n = n + 1
    print("矩形个数 %f" % n)
    sensor.set_framesize(sensor.QVGA)
    return n


# 圆形识别（只能检测边缘有阴影的）
# def Circle_Discern_odl(index):
    # sensor.set_framesize(sensor.QQVGA)
    #img = sensor.snapshot().lens_corr(1.8)
    #n = 0
    # for c in img.find_circles(threshold = 5000, x_margin = 20, y_margin = 20, r_margin = 20,r_min = 30, r_max = 300, r_step = 2):
    #area = (c.x()-c.r(), c.y()-c.r(), 2*c.r(), 2*c.r())
    # statistics = img.get_statistics(roi=area)#像素颜色统计
    # if (index > 0 and index <= len(color_list)):
    #ranges = color_list[index - 1]
    # if ranges[0] < statistics.l_mode() < ranges[1] and ranges[2] < statistics.a_mode() < ranges[3] and ranges[4] < statistics.b_mode() < ranges[5]:
    #n = n + 1
    # else:
    #n = n + 1
    #print("圆形个数 %f" %n)
    # sensor.set_framesize(sensor.QVGA)
    # return n


# 圆形识别
def Circle_Discern():
    sensor.set_brightness(-3)
    sensor.set_saturation(3)
    result_final = [0 for i in range(len(color_list))]
    for m in range(3):
        result = [0 for i in range(len(color_list))]
        for j in range(10):
            img = sensor.snapshot()
            for i in range(3):
                number = 0
                for b in img.find_blobs([color_list[i]], area_threshold=50, merge=True):
                    n = 0
                    for l in img.find_line_segments(roi=[b.x() - 5, b.y() - 5, b.w() + 10, b.h() + 10], merge_distance=26, max_theta_diff=26):
                        if (l.length() < 30):
                            n += 1
                            #img.draw_line(l.line(), color = (255, 0, 0))
                    #img.draw_rectangle(b.rect(), color = (255, 0 ,0))
                    if (n > 3):
                        number += 1
                if (number > result[i]):
                    result[i] = number
        for i in range(len(result)):
            result_final[i] += result[i]
    for i in range(len(result_final)):
        avg = result_final[i] / 5
        if (avg > int(avg) + 0.8):
            result_final[i] = int(avg) + 1
        else:
            result_final[i] = int(avg)
    print("最终结果：", result_final)
    sensor.set_brightness(0)
    sensor.set_saturation(0)
    UART_Send([0x55, 0x02, 0x91, result_final[0], result_final[1], result_final[2], 0x00, 0xBB], 8)



# 颜色个数识别
def Color_Discern(index):
    n = 0
    img = sensor.snapshot()
    if (index > 0 and index <= len(color_list)):
        blobs = img.find_blobs([color_list[index - 1]], merge=True)
        n = len(blobs)
    else:
        blobs = img.find_blobs(color_list, merge=True)
        n = len(blobs)
    print("色块个数 %f" % n)
    UART_Send([0x55, 0x02, 0x91, n, 0x00, 0x00, 0x00, 0xBB], 8)
    return n


# 颜色类型总数识别
def Color_Type_Discern():
    n = 0
    img = sensor.snapshot()
    for i in range(len(color_list)):
        blobs = img.find_blobs([color_list[i]], merge=True)
        if (len(blobs) > 0):
            n = n + 1
    print("色块个数：%f" % n)
    UART_Send([0x55, 0x02, 0x91, n, 0x00, 0x00, 0x00, 0xBB], 8)
    return n


# 获取交通灯颜色
def Get_TrafficLightColor(img):
    for blob in img.find_blobs([red_traffic, yellow_traffic, green_traffic], roi=([0, 0, 320, 120]), area_threshold=300, merge=True):
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        return blob.code()


# 交通灯识别
def Discern_TrafficLight():
    sensor.set_brightness(-3)
    sensor.set_contrast(-3)
    sensor.set_saturation(3)
    traffic_light = 0
    for i in range(1, 100):
        img = sensor.snapshot()
        traffic_light = Get_TrafficLightColor(img)
        if(traffic_light in [1, 2, 4]):
            break
    sensor.skip_frames(tiem=4000)
    sensor.set_brightness(0)
    sensor.set_contrast(0)
    sensor.set_saturation(0)
    sensor.set_auto_gain(True)
    sensor.set_auto_whitebal(True)
    return traffic_light


# 二维码识别
def QRCode_Recognition():
    for i in range(10):
        img = sensor.snapshot()
        for code in img.find_qrcodes():
            content = code.payload()
            return content


# 返回二维码识别结果
def Return_QRCode(result):
    length = len(result)
    UART_Send([0x55, 0x02, 0x92, 0x01, length], 5)
    for i in result:
        uart.writechar(ord(i))
    uart.writechar(0xBB)


#  发送交通灯识别结果
def Return_TrafficLightResult(result):
    if(result == 1):
        result = 1
        print("红色")
    elif(result == 2):
        result = 3
        print("黄色")
    elif(result == 4):
        result = 2
        print("绿色")
    else:
        result = 3
        print("默认：黄色")
    UART_Send([0x55, 0x02, 0x91, result, 0x00, 0x00, 0x00, 0xBB], 8)


# 正常的数据
correctDataTable = [0x55, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xBB]
receiveTable = [0, 0, 0, 0, 0, 0, 0, 0]


# 检查串口数据
def Check_Uart():
    Reset_List(receiveTable)
    uartDataReceived = False
    # 检测串口
    if (uart.any()):
        print("data:")
        # 接收数据头
        for i in range(0, 2):
            receiveTable[i] = uart.readchar()
            # 判断数据头
            if (receiveTable[i] != correctDataTable[i]):
                break
        else:
            # 检查数据头长度
            if (i == 1):
                # 接收数据位
                for j in range(2, 7):
                    receiveTable[j] = uart.readchar()
                    # 判断是否有错误数据
                    if (receiveTable[j] == -1):
                        print("bad data")
                        break
                else:
                    # 判断数据内容长度
                    if (j == 6):
                        # 接收包尾
                        receiveTable[7] = uart.readchar()
                        # 判断包尾
                        if (receiveTable[7] == correctDataTable[7]):
                            uartDataReceived = True
                        else:
                            print("wrong ending")
                    else:
                        print("abnormal length")
            else:
                print("wrong header")

    return uartDataReceived


# 主循环
while (True):

    if (Check_Uart()):
        print(receiveTable)

    # 二维码
    if (receiveTable[Pack_MainCmd] == 0x92):
        print("QRCode Recognition")
        content = QRCode_Recognition()
        if (content):
            print("QRCode Content:" + content)
            Return_QRCode(content)
        else:
            print("QRCode Error")

    # 交通灯、图形
    elif (receiveTable[Pack_MainCmd] == 0x91):
        if (receiveTable[Pack_SubCmd1] == OpenMV_Trafficlight):
            print("Traffic Light")
            color = Discern_TrafficLight()
            Return_TrafficLightResult(color)
        elif (receiveTable[Pack_SubCmd1] == OpenMV_Circle):
            print("Circle")
            Circle_Discern()

        elif (receiveTable[Pack_SubCmd1] == OpenMV_Rectangle):
            # Rect_Discern()
            print("Rectangle")

        elif (receiveTable[Pack_SubCmd1] == OpenMV_ColorNumber):
            print("Color")
            Color_Discern(receiveTable[Pack_SubCmd2])

        elif (receiveTable[Pack_SubCmd1] == OpenMV_AllColorNumber):
            print("ALL Color")
            Color_Type_Discern()

        else:
            print("Undefined action")

# OpenMV_Trafficlight = 0x01
# OpenMV_Circle = 0x02
# OpenMV_Rectangle = 0x03
# OpenMV_ColorNumber = 0x04
# OpenMV_AllColorNumber = 0x05

    #img = sensor.snapshot()
    # lcd.display(img)
