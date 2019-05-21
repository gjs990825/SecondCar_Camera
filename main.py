import sensor
import image
import time
import lcd
from pyb import UART, Timer, LED

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  # 320*240
# sensor.set_auto_gain(True)       #设置自动增益
# sensor.skip_frames(10)           #刷新设置
clock = time.clock()
lcd.init()  # Initialize the lcd screen.
uart = UART(3, 115200, 8, None, 1)  # 创建串口对象

data = []

LED_Red = LED(1)
LED_Green = LED(2)
LED_Blue = LED(3)


red = (40, 72, 52, 81, -7, 60)
yellow = (60, 79, -37, 35, 12, 36)
green = (49, 84, -92, -44, -6, 57)

# create a timer object using timer 4
tim = Timer(4, freq=1)
# tim.callback(tick)
tim.deinit()

FlagOK = 0
show_numTab = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
num = 0
returnData = [0x55, 0x02, 0x92, 0x02, 0x02, 0x00, 0x00, 0xBB]  # 识别失败
runData = [0x55, 0x02, 0x92, 0x03, 0x02, 0x00, 0x00, 0xBB]  # 正在识别


# 定时器回调函数
def tick(timer):            # we will receive the timer object when being called
    global FlagOK, num, returnData
    print("Timer callback")
    num = num-1
    if(num == 0):
        num = 9
        FlagOK = 2
        tim.deinit()


# 串口发送函数
def UART_Send(src, length):
    for i in range(length):
        uart.writechar(src[i])


# 置零list所有成员
def Reset_List(src):
    for i in range(len(src)):
        src[i] = 0


# 交通灯识别
def discern_traffic_light(img):
    for blob in img.find_blobs([red, yellow, green], roi=[0, 0, 320, 240], area_threshold=400, merge=True):
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        lcd.display(img)
        return blob.code()


#   二维码识别，并返回识别结果
def Color_Check(srcbuf):
    global FlagOK, num
    if(FlagOK == 1):
        img.draw_string(100, 180, "open"+show_numTab[num], color=[255, 0, 0])
        for code in img.find_qrcodes():
            FlagOK = 0
            tim.deinit()
            print(code)
            qr_Tab = code.payload()
            uart.writechar(0x55)
            uart.writechar(0x02)
            uart.writechar(0x92)
            uart.writechar(0x01)
            uart.writechar(len(qr_Tab))
            for qrdata in qr_Tab:
                uart.writechar(ord(qrdata))
            uart.writechar(0xBB)

    if(FlagOK == 2):
        for rdata in returnData:
            uart.writechar(rdata)
        FlagOK = 0


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
        print("黄色")

    trafficLightReturn = [0x55, 0x02, 0x91, result, 0x00, 0x00, 0x00, 0xBB]
    UART_Send(trafficLightReturn, 8)


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


while (True):

    if (Check_Uart()):
        print(receiveTable)

    #img = sensor.snapshot()
    # lcd.display(img)

# while(True):

#     img = sensor.snapshot()

    # if(uart.any()):
    #     print("接收")
    #     data = uart.read(4)
    #     if((data[0] == 0x55) and (data[1] == 0x02)):
    #         if(len(data) >= 4):
    #             for d in data:
    #                 print(d)
    #             print("接收成功")

        # if(data[2] == 0x92):
        #     print("识别二维码")
        #     if(data[3] == 0x01):    #启动识别
        #         if(FlagOK == 0):
        #             FlagOK = 1
        #             num = 9
        #             print("开始识别")
        #             tim.callback(tick)
        #         else:
        #             print("正在识别")
        #             for rdata in runData:
        #                 print(rdata)
        #                 uart.writechar(rdata)
        #     if(data[3] == 0x02):
        #         print("停止识别")
        #         FlagOK = 2
        #         tim.deinit()       #定时器停止
        # if(data[2] == 0x91):
        #     print("交通灯识别")
        #     sensor.set_brightness(-3)
        #     sensor.set_contrast(-3)
        #     sensor.set_saturation(3)
        #     traffic_light = 0
        #     for i in range(1, 100):
        #         img = sensor.snapshot()
        #         traffic_light = discern_traffic_light(img)
        #         if(traffic_light in [1, 2, 4]):
        #             break
        #         lcd.display(img)
        #     print(traffic_light)
        #     sensor.skip_frames(tiem = 4000)
        #     sensor.set_brightness(0)
        #     sensor.set_contrast(0)
        #     sensor.set_saturation(0)
        #     Return_TrafficLightResult(traffic_light)

    # Color_Check(data)
    # lcd.display(img)
