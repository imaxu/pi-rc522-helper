#coding=utf-8

from pirc522 import RFID
import time
import struct
from threading import Thread
import inspect
import ctypes

""" 
A class is based on pirc522 lib.
You can install pirc522 with pip what the command is ' pip install pi-rc522 '.

@auth - xuwh
@date - 2018-9-9
@git - https://github.com/imaxu

"""

class PI_RC522_Helper():

    # 最后读到的十进制卡号
    last_uid = None
    # 当前卡号
    current_uid = None
    # RFID instance
    rdr = None
    # 卡进入事件
    on_move_in = None
    # 卡移除事件
    on_move_out = None
    # 监听间隔，类型为浮点小数，单位秒。该参数对读卡精确度有影响，建议在0.25-0.3之间
    wait_time = 0.3


    def __init__(self):
        self.rdr = RFID()
        self.last_uid = 0
        self.current_uid = 0

    def scan(self,onIn,onOut):
        self.on_move_in = onIn
        self.on_move_out = onOut

        scan_thread = Thread(target=self.__scan__)
        try:
            scan_thread.start()
            self.__check__()
        except KeyboardInterrupt:
            self.__async_raise__(scan_thread.ident, SystemExit)
            print("退出读卡进程")
        finally:
            self.rdr.cleanup()
        pass



    def __async_raise__(self,tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")


    def __scan__(self):
        while True:
            self.rdr.wait_for_tag()
            state,tag_type = self.rdr.request()
            if not  state:
                state,uid = self.rdr.anticoll()
                if not state:
                    self.current_uid = struct.unpack('<L',bytes(uid[0:4]))[0]
                    continue
            self.current_uid = 0

    def __check__(self):
        while True:
            time.sleep(self.wait_time)
            if self.current_uid == 0:
                if self.current_uid != self.last_uid:
                    self.last_uid = 0
                    if self.on_move_out:
                        self.on_move_out()
            else:
                if self.current_uid != self.last_uid:
                    self.last_uid = self.current_uid
                    if self.on_move_in:
                        self.on_move_in(self.current_uid)

# test demo                

def onCardIn(uid):
    print("识别到卡号->",uid)

def onCardOut():
    print("<--卡移出")    

def main():
    helper = PI_RC522_Helper()
    helper.scan(onCardIn,onCardOut)


if __name__ == '__main__':
    main()