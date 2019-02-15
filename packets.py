#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

#TODO: enforce type checking and maybe type operations
class packet():

    def __init__(self,start_code=0x55, start_code2 = 0xAA, device_ID = 0x0001):
        self.start_code = start_code
        self.start_code2 = start_code2
        self.device_ID = device_ID

    def rightShift(self ,n, x):
        return (n >> x & 0xFF)

    def leftShift(self ,n, x):
        #print("Byte: " + str(n) + ", Shift: " + str(x))
        return (n << x & 0xFFFF)

    def checksum_calc(self,packet_bytes):
        byte_sum = 0
        for i in range(0,len(packet_bytes)):
            byte_sum += packet_bytes[i]
        return byte_sum & 0xFFFF

    def debbug_Package(self,packet_bytes):
        for i in range(0,len(packet_bytes)):
            print(hex(packet_bytes[i]),end = " ")
            #print("a")
        return True        
    

class command_packet(packet):

    def __init__(self, parameter,command,checksum = 0):
        super().__init__()
        self.parameter = parameter        
        self.command = self.command_dict[command]
        self.packet_bytes = self.mount_packet()        

    def debbug_Package(self):
        return packet.debbug_Package(self,self.packet_bytes)

    def mount_packet(self):
        packet_bytes = bytearray(12)

        packet_bytes[0] = self.start_code
        packet_bytes[1] = self.start_code2
        packet_bytes[2] = self.rightShift(self.device_ID,0)
        packet_bytes[3] = self.rightShift(self.device_ID,8)
        packet_bytes[4] = self.rightShift(self.parameter,0)
        packet_bytes[5] = self.rightShift(self.parameter,8)
        packet_bytes[6] = self.rightShift(self.parameter,16)
        packet_bytes[7] = self.rightShift(self.parameter,24)
        packet_bytes[8] = self.rightShift(self.command,0)
        packet_bytes[9] = self.rightShift(self.command,8)
        self.checksum = self.checksum_calc(packet_bytes)
        packet_bytes[10] = self.rightShift(self.checksum,0)
        packet_bytes[11] = self.rightShift(self.checksum,8)

        return packet_bytes

    command_dict = {
    "OPEN"                  : 0x01,
    "CLOSE"                 : 0x02,
    "USB_INTERNAL_CHECK"    : 0x03,
    "CHANGE_BAUDRATE"       : 0x04,
    "MODULE_INFO"           : 0x06,
    
    "CMOS_LED"              : 0x12,

    "ENROLL_COUNT"          : 0x20,
    "CHECK_ENROLLED"        : 0x21,
    "ENROLL_START"          : 0x22,
    "ENROLL1"               : 0x23,
    "ENROLL2"               : 0x24,
    "ENROLL3"               : 0x25,
    "IS_PRESS_FINGER"       : 0x26,
    
    "DELETE_ID"             : 0x40,
    "DELETE_ALL"            : 0x41,
    
    "VERIFY"                : 0x50,
    "IDENTIFY"              : 0x51,
    "VERIFY_TEMPLATE"       : 0x52,
    "IDENTIFY_TEMPLATE"     : 0x53,
    
    "CAPTURE"               : 0x60,

    "MAKE_TEMPLATE"         : 0x61,

    "GET_IMAGE"             : 0x62,
    "GET_RAWIMAGE"          : 0x63,
    
    "GET_TEMPLATE"          : 0x70,
    "SET_TEMPLATE"          : 0x71,
    #code for ADD_TEMPLATE in the documentation is the code for SET_TEMPLATE
    "GET_DATABASE_START"    : 0x72,
    "GET_DATABASE_END"      : 0x73,
    
    "FW_UPDATE"             : 0x80,
    "ISO_UPDATE"            : 0x81,
    "FAKE_DETECTOR"         : 0x91,

    "SET_SECURITY_LEVEL"    : 0xF0,
    "GET_SECURITY_LEVEL"    : 0xF1,
    
    "IDENTIFY_TEMPLATE_2"   : 0XF4,

    "STANDBY_MODE"   : 0XF9, #low power consumption

    "ACK_OK"                : 0x30,
    "NACK_INFO"             : 0x31
    }

class response_packet(packet):
    def __init__(self,received_bytes):
        super().__init__()
        #self.print_received_bytes(received_bytes)
        self.set_Attr(received_bytes)
        self.packet_bytes = self.mount_packet(received_bytes)
    
        
    def print_received_bytes(self,received_bytes):
        for i in range(0,12):
            print(str(hex(received_bytes[i])), end= " ")
        print(" ")
        
    def set_Attr(self,received_bytes):
        self.parameter = self.leftShift(received_bytes[7],24) | self.leftShift(received_bytes[6],16) | self.leftShift(received_bytes[5],8) | self.leftShift(received_bytes[4],0)
        self.response  = self.leftShift(received_bytes[9],8) | self.leftShift(received_bytes[8],0) 
        
    def debbug_Package(self):
        return packet.debbug_Package(self,self.packet_bytes)
    
    def compare_checksum(self,received_bytes):
        rcvd_checksum = self.leftShift(received_bytes[11],8) | received_bytes[10]
        if (rcvd_checksum != self.checksum):
            raise ValueError("Invalid checksum !")
        return True

    def response_print(self):
        """
        Prints the response in an easy to read manner, for easy debbuging of function calls
        """
        if(self.response == 0x30):
            print("ACK: OK ", end = "")
            print("DATA: " + str(self.parameter))

        elif (self.response == 0x31):
            print("ACK: NOTOK ", end = "")
            inv_map = {v: k for k, v in self.error_response_dict.items()}
            if(self.parameter in inv_map):
                print("PARAMETER: " + str(inv_map[self.parameter]))
            elif(0<= self.parameter <=2999):
                print("PARAMETER: DUPLICATED_ID")
            else:
                print("PARAMETER: " + str(hex(self.parameter)))
                raise ValueError("Invalid parameter")
        else:
            raise ValueError("Invalid response code!")

    def mount_packet(self,received_bytes):
        packet_bytes = bytearray(12)

        packet_bytes[0] = self.start_code
        packet_bytes[1] = self.start_code2
        packet_bytes[2] = self.rightShift(self.device_ID,0)
        packet_bytes[3] = self.rightShift(self.device_ID,8)
        packet_bytes[4] = self.rightShift(self.parameter,0)
        packet_bytes[5] = self.rightShift(self.parameter,8)
        packet_bytes[6] = self.rightShift(self.parameter,16)
        packet_bytes[7] = self.rightShift(self.parameter,24)
        packet_bytes[8] = self.rightShift(self.response,0)
        packet_bytes[9] = self.rightShift(self.response,8)
        self.checksum = self.checksum_calc(packet_bytes)
        self.compare_checksum(received_bytes)
        packet_bytes[10] = self.rightShift(self.checksum,0)
        packet_bytes[11] = self.rightShift(self.checksum,8)

        return packet_bytes


    #TODO: Watch out for the duplicated id_NACK
    error_response_dict = {
        "NACK_TIMEOUT"               : 0x1001,              
        "NACK_INVALID_BAUDRATE"      : 0x1002,      
        "NACK_INVALID_POS"           : 0x1003,          
        "NACK_IS_NOT_USED"           : 0x1004,          
        "NACK_IS_ALREADY_USED"       : 0x1005,      
        "NACK_COMM_ERR"              : 0x1006,              
        "NACK_VERIFY_FAILED"         : 0x1007,          
        "NACK_IDENTIFY_FAILED"       : 0x1008,      
        "NACK_DB_IS_FULL"            : 0x1009,              
        "NACK_DB_IS_EMPTY"           : 0x100A,          
        "NACK_TURN_ERR"              : 0x100B,              
        "NACK_BAD_FINGER"            : 0x100C,
        "NACK_ENROLL_FAILED"         : 0x100D,
        "NACK_IS_NOT_SUPPORTED"      : 0x100E,
        "NACK_DEV_ERR"               : 0x100F,
        "NACK_CAPTURE_CANCELED"      : 0x1010,
        "NACK_INVALID_PARAM"         : 0x1011,
        "NACK_FINGER_IS_NOT_PRESSED" : 0x1012
    }

class data_packet (packet):
    def __init__(self,received_bytes):
        self.start_code = 0x5A
        self.start_code2 = 0xA5
        self.device_ID = 0x0001
        self.data = list()
        self.set_Data(received_bytes)
        self.packet_bytes = self.mount_packet(received_bytes)

    def data_Print(self):
        last_index = len(self.packet_bytes)
        print("DATA: [ " + str(hex(self.packet_bytes[4])),end="")
        for i in range(4,len(self.packet_bytes)):
            print(", " + str(hex(self.packet_bytes[i])),end="")
        print("]")
        print("CHECKSUM: [" + str(hex(self.packet_bytes[last_index -1])) +"," + str(hex(self.packet_bytes[last_index -2]))+"]")
    
    def set_Data(self,received_bytes):
        for i  in range(4,len(received_bytes) - 2):
            self.data.append(received_bytes[i])

    def compare_checksum(self,received_bytes):
        pos = len(received_bytes)
        rcvd_checksum = self.leftShift(received_bytes[pos-1],8) | received_bytes[pos-2]
        
        if (rcvd_checksum != self.checksum):
            print(str(hex(self.checksum)) + " | " + str(hex(rcvd_checksum)) )
            raise ValueError("Invalid checksum !")
        return True

    def mount_packet (self,received_bytes):
        size = len(received_bytes)
        packet_bytes = bytearray(size)

        packet_bytes[0] = self.start_code
        packet_bytes[1] = self.start_code2
        packet_bytes[2] = self.rightShift(self.device_ID,0)
        packet_bytes[3] = self.rightShift(self.device_ID,8)

        last_index = len(received_bytes)
        for i in range(4,last_index - 2):
            packet_bytes[i] = received_bytes[i]

        self.checksum = self.checksum_calc(packet_bytes)
        self.compare_checksum(received_bytes)
        
        packet_bytes[last_index-2] = self.rightShift(self.checksum,0)
        packet_bytes[last_index-1] = self.rightShift(self.checksum,8)

        return packet_bytes