# Untitled - By: STM32 - 周四 四月 19 2018


import sensor, image,time,lcd
from pyb import UART,Timer,LED

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)#320*240

sensor.skip_frames()
sensor.set_auto_whitebal(False)      #关闭白平衡
sensor.set_auto_gain(False)          #关闭自动增益
clock = time.clock()
lcd.init()                           #Initialize the lcd screen.
uart = UART(3,115200,8,None,1)       #创建串口对象

data = []

LED_Red = LED(1)
LED_Green = LED(2)
LED_Blue = LED(3)


tim = Timer(4,freq=1)              # create a timer object using timer 4
#tim.callback(tick)
tim.deinit()

FlagOK = 0
show_numTab = ["0","1","2","3","4","5","6","7","8","9"]
num = 0
returnData = [0x55,0x02,0x92,0x02,0x02,0x00,0x00,0xBB]  #识别失败
runData    = [0x55,0x02,0x92,0x03,0x02,0x00,0x00,0xBB]  #正在识别

#定时器回调函数
def tick(timer):            # we will receive the timer object when being called
    global FlagOK,num,returnData
    print("Timer callback")
    num = num-1
    if(num == 0):
        num = 9
        FlagOK = 2
        tim.deinit()

#串口发送函数
def USART_Send(src,length):
    for i in range(length):
        uart.writechar(src[i])


#   二维码识别，并返回识别结果
def Color_Check(srcbuf):
    global FlagOK,num
    if(FlagOK == 1):
        img.draw_string(100, 180,"open"+show_numTab[num],color=[255,0,0])
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


while(True):


    img = sensor.snapshot()

    if(uart.any()):
        data = uart.read(8)
        if( len(data) >= 8):
            if((data[0] == 0x55)&(data[1] == 0x02)&(data[7] == 0xBB)):
                if(data[2] == 0x91):
                    print("识别小球")
                if(data[2] == 0x92):
                    print("识别二维码")
                    if(data[3] == 0x01):    #启动识别
                        if(FlagOK == 0):
                            FlagOK = 1
                            num = 9
                            print("开始识别")
                            tim.callback(tick)
                        else:
                            print("正在识别")
                            for rdata in runData:
                                print(rdata)
                                uart.writechar(rdata)
                    if(data[3] == 0x02):
                        print("停止识别")
                        FlagOK = 2
                        tim.deinit()       #定时器停止

    Color_Check(data)

    img.draw_string(110, 40,"qr_CodeV1.0",color=[0,0,255])
    lcd.display(img)


