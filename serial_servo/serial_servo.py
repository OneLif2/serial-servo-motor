from .serial import Serial_rw
from .ra_error import *


class Servo():
    def __init__(self, ID):
        self.srw = Serial_rw(ID)
        self.ID = ID
        self.pos = None
        self.speed = 0

        self.read_goal_pos = 0
        self.read_curr_pos = 0
        self.read_pos_ctr = 0
        self.read_pos_ctr_offset = 0
        self.read_move_status = 0

        self.READ_CMD = 0x02
        self.WRITE_CMD = 0x03
        self.MAX_POS_LMT = 0xB # 2 bytes
        self.WORK_MODE = 0x21 # 2 bytes
        self.GOAL_POS = 0x2A  # 2 bytes
        self.SPEED = 0x2E
        self.CURR_POS = 0x38  # 2 bytes
        self.MOVE_STATUS = 0x42  # 1 bytes
        self.POS_COUNTER = 0x43  # 1 bytes

    def sint2u16(self, signed_int):
        u16 = signed_int % 2**16
        return u16
    
    def sint2s16(self, signed_int):
        s16 = (signed_int + 2**15) % 2**16 - 2**15
        return s16
    
    def clamp(self, n, minn, maxn):
        return max(min(maxn, n), minn)

    def str2arr(self, newdata_hex, split_strings):
        for index in range(0, len(newdata_hex), 2):
            split_strings.append(int(newdata_hex[index: index + 2], 16))
    
    def hexdata(self, a):
        print('[{}]'.format(', '.join(hex(x) for x in a)))   

    def change_mod(self, mode):
        if mode == 0:
            int_arr = [0xFF, 0xFF, self.ID, 4, self.WRITE_CMD, 33, mode, 0x00]
            self.srw.send(int_arr)
            int_arr = [0xFF, 0xFF, self.ID, 5, self.WRITE_CMD, 11, 0xff, 0xf, 0x00]
            self.srw.send(int_arr)
            self.read_all_info()
            print("ID ", self.ID, " change mode", mode, "ok")
        if mode == 3:
            int_arr = [0xFF, 0xFF, self.ID, 4, self.WRITE_CMD, 33, mode, 0x00]
            self.srw.send(int_arr)
            int_arr = [0xFF, 0xFF, self.ID, 5, self.WRITE_CMD, 11, 0x00, 0x00, 0x00]
            self.srw.send(int_arr)
            self.read_all_info()
            self.read_pos_ctr_offset = self.read_pos_ctr
            print("ID ", self.ID, " change mode", mode, "ok")

    def sint2pos(self,signed_int:int):
        if signed_int <0:
            signed_int = abs(signed_int) + 0x8000
        return signed_int

    def pos2sint(self,unsiged_int:int):
        if unsiged_int > 0x8000:
            unsiged_int = 0x8000 - unsiged_int
        return unsiged_int

    def servo_pos_spd(self, pos, speed):
        #32768 = -0, #32769= - 1
        #max pos = -360*8 to 360*8
        self.speed = speed
        self.pos = self.sint2pos(round(self.clamp(pos,-360*8,360*8)/360*4095))
        int_arr = [0xFF, 0xFF, self.ID, 9, self.WRITE_CMD, self.GOAL_POS, self.pos % 256, (self.pos >> 8) % 256, 0, 0,
                   int(self.speed) % 256, int(self.speed) >> 8, 0x00]
        self.srw.send(int_arr)
    
    def servo_pos(self, pos):
        self.pos = self.sint2u16(round(self.clamp(pos,-360*8,360*8)/360*4095))
        print(pos)
        print(int(pos/360*4095))
        print(hex(self.pos))
        int_arr = [0xFF, 0xFF, self.ID, 5, self.WRITE_CMD, self.GOAL_POS, self.pos % 256, self.pos >> 8, 0x00]
        self.srw.send(int_arr)

    def setSpeed(self, speed: int):
        self.speed = speed
        int_arr = [0xFF, 0xFF, self.ID, 5, self.WRITE_CMD, self.SPEED, int(self.speed) % 256, int(self.speed) >> 8, 0x00]
        self.srw.send(int_arr)
        print("Set speed ok !")

    def isMoving(self):
        gp, cp, pc, m = self.read_mv_status()
        #self.read_all_info()
        print("ID : ", self.ID, " | read_goal_pos = ", gp," | read_pres_pos = ", cp, "  | read_pos_counter = ", pc, "| read_move_status = ", m)
        if m == 1:
            return True  # return 1009 while it is moving
        if m == 0:
            return False  # return 0 while stopped
        raise RAError() 

    def calculate_checksum(self, int_arr):
        checksum = 0
        for i in int_arr[2:-1]:
            checksum += i
        return (checksum & 255) ^ 255 == int_arr[-1]

    def read_mv_status(self):
        split_strings = []
        read_arr = [0xff, 0xff, self.ID, 0x4, 0x2, 0x2a, 0x21, 0x00]
        newdata_hex = self.srw.get_data(read_arr)
        self.str2arr(newdata_hex, split_strings)
        #self.hexdata(split_strings)
        if self.calculate_checksum(split_strings) == True:
            self.read_goal_pos = self.pos2sint(split_strings[self.GOAL_POS - 0x25] | (split_strings[self.GOAL_POS - 0x24] << 8))
            self.read_curr_pos = self.pos2sint(split_strings[self.CURR_POS - 0x25] | (split_strings[self.CURR_POS - 0x24] << 8))
            self.read_pos_ctr = (self.pos2sint(split_strings[self.POS_COUNTER - 0x25] | (split_strings[self.POS_COUNTER- 0x24] << 8))) - self.read_pos_ctr_offset
            self.read_move_status = split_strings[self.MOVE_STATUS - 0x25]
        return self.read_goal_pos, self.read_curr_pos, self.read_pos_ctr, self.read_move_status
    
    def clear_turns_no(self):
        split_strings = []
        clear_arr = [0xFF, 0xFF, self.ID, 0x05, self.WRITE_CMD, self.POS_COUNTER, 0x00, 0x00, 0x00]
        newdata_hex = self.srw.send(clear_arr)
        self.str2arr(newdata_hex, split_strings)
        #self.hexdata(split_strings)

    def read_all_info(self):
        split_strings = []
        read_arr = [0xff, 0xff, self.ID, 0x4, self.READ_CMD, 0, 87, 0x00]
        newdata_hex = self.srw.get_data(read_arr)
        self.str2arr(newdata_hex, split_strings)
        #self.hexdata(split_strings[6:26])
        #self.hexdata(split_strings[26:46])
        #self.hexdata(split_strings[46:66])
        #self.hexdata(split_strings[66:86])
        #self.hexdata(split_strings[86:])
        #print(len(split_strings)-6)
        if self.calculate_checksum(split_strings) == True:
            del split_strings[0:5]
            read_work_mode = split_strings[self.WORK_MODE]
            self.read_max_pos_mlt = split_strings[self.MAX_POS_LMT]  | split_strings[self.MAX_POS_LMT+1]  << 8
            self.read_goal_pos = self.pos2sint(split_strings[self.GOAL_POS] | (split_strings[self.GOAL_POS+1] << 8))
            self.read_curr_pos = self.pos2sint(split_strings[self.CURR_POS] | (split_strings[self.CURR_POS+1] << 8))
            self.read_pos_ctr = (self.pos2sint(split_strings[self.POS_COUNTER] | (split_strings[self.POS_COUNTER+1] << 8))) - self.read_pos_ctr_offset
            self.read_move_status = split_strings[self.MOVE_STATUS]
        print("ID",self.ID,"WM:",'Stepper' if read_work_mode == 3 else 'Servo', ",goal pos =",self.read_goal_pos, ",curr pos =",self.read_curr_pos, ",pos counter =",self.read_pos_ctr, ",IsMoving =",self.read_move_status)
        return read_work_mode, self.read_max_pos_mlt, self.read_goal_pos, self.read_curr_pos, self.read_pos_ctr, self.read_move_status


"""
    def moveJoint(self, jPos):
        msg = 'MoveJ,0,' \
            + str(jPos.j1) + ',' + str(jPos.j2) + ',' \
            + str(jPos.j3) + ',' + str(jPos.j4) + ',' \
            + str(jPos.j5) + ',' + str(jPos.j6) + ',;'
        reply = self.srw.send(msg)
        self._validate(reply)
    
    def setSpeed(self, speed: int):
        msg = 'SetOverride,0,' \
            + str(speed) + ',;'
        reply = self.srw.send(msg)
        self._validate(reply)

    def getSpeed(self) -> int:
        msg = 'ReadOverride,0,;'
        reply = self.srw.send(msg)
        self._validate(reply)
        values = reply.split(',')
        if len(values) < 4:
            raise RAError('Received invalid response.')
        return values[2]
        
    def moveGripper(self, position, speed=250, force=10):
        self.clamp(position,0,140)
        self.clamp(speed,30,250)
        self.clamp(force,10,125)
        msg = 'SetRobotiq,' + str(position) + ',' + str(speed) + ',' + str(force) + ',;'
        reply = self.srw.send(msg)
        self._validate(reply)
    
    def resetGripper(self):
        msg = 'RobotIQReset,;'
        reply = self.srw.send(msg)
        self._validate(reply) #check if error raised
        print(reply)

    def isGripperMoving(self):
        reply = self.srw.send('RobotiqStatus,;')
        self._validate(reply)
        if reply == 'RobotiqStatus,OK,0,3,1,1,;':
            return True #return True while its moving
        if reply == 'RobotiqStatus,OK,2,3,1,1,;':
            return False #return True while it is grasping an object    
        if reply == 'RobotiqStatus,OK,3,3,1,1,;':
            return False #return False when the action is done
        raise RAError()
"""
