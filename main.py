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
OpenMV_ShapeRecogniction = 0x02

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  # 320*240
# sensor.set_auto_gain(True)       #设置自动增益
# sensor.skip_frames(10)           #刷新设置
# Initialize the lcd screen.
lcd.init()
# 创建串口对象
uart = UART(3, 115200, 8, None, 1)


# LED对象创建
LED_Red = LED(1)
LED_Green = LED(2)
LED_Blue = LED(3)

# 颜色阈值设定
red = (40, 72, 52, 81, -7, 60)
yellow = (60, 79, -37, 35, 12, 36)
green = (49, 84, -92, -44, -6, 57)


# 串口发送函数
def UART_Send(src, length):
    for i in range(length):
        uart.writechar(src[i])


# 置零list所有成员
def Reset_List(src):
    for i in range(len(src)):
        src[i] = 0


# 获取交通灯颜色
def Get_TrafficLightColor(img):
    for blob in img.find_blobs([red, yellow, green], area_threshold=400, merge=True):
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
            print("Traffic Light Recognition")
            color = Discern_TrafficLight()
            Return_TrafficLightResult(color)
        else:
            print("Undefined action")
    #img = sensor.snapshot()
    #lcd.display(img)
