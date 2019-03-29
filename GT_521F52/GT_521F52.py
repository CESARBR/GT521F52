#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import serial
import struct
from . import packets
import time
import logging


#For using and parsing the shell command
import subprocess
import shlex

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


#Script that gives me the baud of the scan'
def get_baudrate_from_SCAN(device):
    command = 'stty -F {0}'.format(device)
    proc_retval = subprocess.check_output(shlex.split(command))
    baudrate = int(proc_retval.split()[1])
    return baudrate

class PyFingerprint_GT_521F52(object):
    """
        This is the class that initiates the conversation with the fp_scanner GT-521F52.
        @param port the address of the scanner
        @param baudRate the desired baud
    """
    __serial = None
#TODO: Are @password and @address realy necessary for this sensor?
    def __init__(self, port = '/dev/ttyUSB0', baudRate = 9600):
  
        if ( os.path.exists(port) == False ):
            raise ValueError('The fingerprint sensor port "' + port + '" was not found!')

        if ( baudRate < 9600 or baudRate > 115200 or baudRate % 9600 != 0 ):
            raise ValueError('The given baudrate is invalid!')

        ## Initialize PySerial connection

        baudRate = get_baudrate_from_SCAN(port)

        logger.debug('Starting conversation with fp_scan, at %s and baud %s' % (port,baudRate))
        
        self.__serial = serial.Serial(port = port, baudrate = baudRate, bytesize = serial.EIGHTBITS, timeout = 2)

        if ( self.__serial.isOpen() == True ):
            self.__serial.close()

        self.__serial.open()
        self.open()
        self.change_Baud_Rate(115200)
        
        logger.debug('Successfully connected to fp_scanner.')

        
    def __del__(self):
        """
        Destructor
        """
        ## Close connection if still established
        if ( self.__serial is not None and self.__serial.isOpen() == True ):
            self.__serial.close()

    def __byteToString(self,byte):
        return struct.pack('@B', byte)
    
    def __stringToByte(self, string):
        return struct.unpack('@B', string)[0]
    
    def writePacket(self,cmd_packet):
        """
        Receives a commmand packet as input and writes it to serial.
        """
        logger.debug('Started writing command_packet bytes.')

        ## Write header (one byte at once)
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[0]))
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[1]))

        # Writing the device_ID parameter
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[2]))
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[3]))
        
        # Writing the parameter parameter
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[4]))
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[5]))
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[6]))
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[7]))
        
        # Writing the command parameter
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[8]))
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[9]))
        
        # Writing the checksum parameter
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[10]))
        self.__serial.write(self.__byteToString(cmd_packet.packet_bytes[11]))
        logger.debug('Finished writing  command_packet bytes.')

    def writeData(self,data):
        """
        Receives a DATA packet and writes it to serial.
        """
        logger.debug('Started writing  data_packet bytes.')
        
        #print("")
        for i in range(0,len(data.packet_bytes)):
        #    print(str(hex(data.packet_bytes[i])),end = " ")
            self.__serial.write(self.__byteToString(data.packet_bytes[i]))
        #print("")

        logger.debug('Finished writing data_packet bytes.')

    
    #read is not reading after changing baud
    def readPacket(self,response_len):
        """
        Reads serial until the expected lenght has been reached.
        """
        logger.debug('Started reading a packet bytes.')

        receivedPacketData = []
        i = 0
        while (i<response_len):
            receivedFragment = self.__serial.read()
            if ( len(receivedFragment) != 0 ):
                receivedFragment = self.__stringToByte(receivedFragment)
                #print ('Received packet fragment = ' + hex(receivedFragment))
                
            receivedPacketData.insert(i, receivedFragment)
            i += 1

        logger.debug('Finished reading packet bytes.')        

        return receivedPacketData     

    def generic_Command(self,param,command_Name):
        """
        Receives the command name and the parameter, mounts the package and writes it to serial.
        It also reads the response of the fp sensor.

        @param param the parameter of the command
        @param command_Name the command that ought to be executed
        @return the response_packet of the scanner
        """
        logger.debug('Executing Generic_Command.')

        cmd_packet = packets.command_packet(param, command_Name)
        self.writePacket(cmd_packet)    
        response_packet = packets.response_packet(self.readPacket(12))

        logger.debug('Generic_Command executed.')

        return response_packet

    def open(self,param = 0x00):
        """
        Opens the scanner for serial communication
        
        @param the param can be 0 or non-zero, if it's zero
        the scanner is initialized and returns nothing, if it's
        non zero it retrieves certain information (firmware version,
        Maximum size of ISO CD image and the deviceSerial number).
       
        @return either nothing or the  requested information.
        """
        logger.debug('Open command started.')

        response_packet = self.generic_Command(param,"OPEN")

        if(response_packet.response == 0x30):
            logger.debug('Open command ended.')
            return True
        elif(response_packet.response == 0x31):
            logger.warning('Open command ended.')
            return False
        else:
            raise ValueError("This response code is invalid.")

    def close(self):
        """
        Closes(?) the connection to the serial.
        
        @return ACK. 
        """
        logger.warning('Close command started.')

        response_packet = self.generic_Command(0x04,"CLOSE")
        
        if (response_packet.response == 0x30):
            logger.debug('Close command ended.')
            return True
        elif(response_packet.response == 0x31):
            logger.warning('Close command failed.')
            return False
        else:
            raise ValueError("This response code is invalid.")
            

    def usb_Internal_Check(self):
        """
        Since the device operates as a removable CD drive, if another removable
        CD drive exists, connection time maybe will be long. To prevent this, call
        this function for fast searching of the device.
        """
        logger.debug('USB internal check started.')

        response_packet = self.generic_Command(0x00,"USB_INTERNAL_CHECK")
        if(response_packet.response == 0x30 and response_packet.parameter == 0x55):
            logger.debug('USB internal check ended sucessfully.')
            return True
        else:
            raise ValueError("This response code is invalid.")

#TODO: FIX -> After updating the baudrate the serial cant communicate with the sensor
    def change_Baud_Rate(self,new_Baud):
        """
        Changes the baud of the scanner to the desired new_Baud, the sensor
        ALWAYS starts with baud == 9600.

        @param new_Baud is the desired new baudrate.
        @return True if everything went right
        @raises ValueError if received an invalid baudrate.
        """
        logger.debug('Baud_rate_change started.')

        if not (new_Baud%9600 == 0 and new_Baud!=28800 and new_Baud!= 48000 and new_Baud != 67200 and new_Baud != 76800 and new_Baud!=86400 and new_Baud != 96000 and new_Baud!=105600):
            raise ValueError("Invalid baudrate.")
            
        response_packet = self.generic_Command(new_Baud,"CHANGE_BAUDRATE")
        
        if (response_packet.response == 0x30):
            self.__serial.baudrate = new_Baud
            logger.debug('Baud_rate_change ended.')
            return True    
        
        elif (response_packet.response == 0x31 and response_packet.parameter == response_packet.error_response_dict["NACK_INVALID_BAUDRATE"]):
            raise ValueError("Invalid baudrate.")
        else:
            raise ValueError("This response code is invalid.")
            

    def set_Led(self):
        """
        Sets the led light ON.
        
        @return True if everything went alright
        @raises ValueError if something went wrong(corrupt packet)
        """
        logger.debug('Set_Led started.')            

        response_packet = self.generic_Command(0x01,"CMOS_LED")
        
        if (response_packet.response == 0x30):
            logger.debug('Set_Led ended.')                        
            return True
        else:
            raise ValueError("This response code is invalid.")
            
    def off_Led(self):
        """
        Sets the led light OFF.
        
        @return True if everything went alright
        @raises ValueError if something went wrong(corrupt packet)
        """
        logger.debug('Off_Led started.')            

        response_packet = self.generic_Command(0x00,"CMOS_LED")

        if (response_packet.response == 0x30):
            logger.debug('Off_Led ended.')            
            return True
        else:
            raise ValueError("This response code is invalid.")

    def enroll_Count(self):
        """
        Returns the number of enrolled fingerprints.

        @return the number of enrolled fingerprints.
        @raises ValueError if receives a invalid response code.
        """
        logger.debug("Enroll_count started")

        response_packet = self.generic_Command(0x00,"ENROLL_COUNT")

        if (response_packet.response == 0x30):
            logger.debug("Enroll_count ended")
            return response_packet.parameter
        else:
            raise ValueError("This response code is invalid.")


    def is_Press_Finger(self):
        """
        Checks wether or not there is a finger on the scanner.
        
        @return 0 if there is a finger pressing the scanner and NoN-zero otherwise.
        @raises ValueError if receives a invalid response code.        
        """
        logger.debug("Is_Press_Finger started")
        response_packet = self.generic_Command(0x00,"IS_PRESS_FINGER")
        if(response_packet.response == 0x30):
            logger.debug("Is_Press_Finger ended")
            return response_packet.parameter 
        else:
            raise ValueError("This response code is invalid.")
              

    def check_Enrolled(self, user_id):        
        """
        This function checks wether a slot is avaiable or not.
      
        @param user_id is the id of the slot that is going to have it's avaiability checked.
        @return True if ID is enrolled and False otherwise.
        @raises ValueError if it received a invalid position.
        """
        logger.debug("Check_Enrolled started")

        response_packet = self.generic_Command(user_id,"CHECK_ENROLLED")
        
        if(response_packet.response == 0x30):
            logger.debug("Check_Enrolled ended.")
            return False

        elif(response_packet.response == 0x31):
            if(response_packet.parameter == response_packet.error_response_dict["NACK_INVALID_POS"]):
                raise ValueError("The position must be between 0-2999.")
            if(response_packet.parameter == 0x1004):
                logger.debug("Check_Enrolled ended.")
                return True                
            logger.debug("Check_Enrolled failed.")

    def Enroll_Start(self, user_id):
        """
        Before an enroll_request is issued, this function must be
        called to check if it's possible or not to store the fingerprint.
        If the parameter is -1 the enrolled finger is not going to be saved on the cache
        and is going to be retrieved as an object instead. The response packet
        may be an ACK (everything is ok) or a NACK (error), the NACK may be one of 
        three types NACK_DB_IS_FULL, NACK_INVALID_POS and NACK_IS_ALREADY_USED (which
        can be checked in the response_packet parameter).
        
        @param user_id is the position chosen for the user to store the fingerprint
        @return True if everything was alright
        @raises ValueError if DB is full, given invalid position or the position is already occupied.
        """
        logger.debug("Enroll_Start started.")

        response_packet = self.generic_Command(user_id,"ENROLL_START")
        
        if (response_packet.response == 0x30):
            logger.debug("Enroll_Start ended.")
            return True
        
        elif(response_packet.response == 0x31):
            if(response_packet.parameter == response_packet.error_response_dict["NACK_DB_IS_FULL"]):
                raise ValueError("Cant enroll, database is full.")
            elif(response_packet.parameter == response_packet.error_response_dict["NACK_INVALID_POS"]):
                raise ValueError("Invalid position.")
            elif(response_packet.parameter == response_packet.error_response_dict["NACK_IS_ALREADY_USED"]):
                raise ValueError("This position is already occupied.")

            logger.warning("Enroll_Start failed.")
                
    def CaptureFinger_Enroll(self):
        """
        Takes a high quality picture of the fingerprint, used
        for better DATA quality (enrollement)

        @return True if everything went correctly
        @raises ValueError if no finger was on the scanner
        """
        logger.debug("CaptureFinger_Enroll started.")

        response_packet = self.generic_Command(0x01,"CAPTURE")
        
        if(response_packet.response == 0x30):
            logger.debug("CaptureFinger_Enroll ended.")
            return True
        elif(response_packet.response == 0x31):
            if(response_packet.parameter == 0x1018):
                raise ValueError("No finger on scanner.")
            logger.warning("CaptureFinger_enrolled failed.")
        
    def CaptureFinger_Identification(self):
        """
        Takes a decent quality picture of the fingerprint, used
        for faster user sensibility (verification)
        
        @return True if everything went correctly
        @raises ValueError if no finger was on the scanner
        """
        logger.debug("CaptureFinger_Identification started.")

        response_packet = self.generic_Command(0x00,"CAPTURE")
        
        if(response_packet.response == 0x30):
            logger.debug("CaptureFinger_Identification ended.")
            return True
        
        elif(response_packet.response == 0x31):
            if(response_packet.parameter == 0x1018):
                raise ValueError("No finger on scanner.")
            logger.warning("CaptureFinger_Identification failed.")


    def delete(self,user_id):
        """
        Deletes the fingerprint located at user_id.
       
        @return True if the delete was sucessfull
        @raises ValueError if the received position was invalid.
        """
        logger.debug("Delete started.")
        response_packet = self.generic_Command(user_id,"DELETE_ID")
        if(response_packet.response == 0x30):
            logger.debug("Delete ended.")
            return True

        elif(response_packet.response == 0x31):
            if(response_packet.parameter == response_packet.error_response_dict["NACK_INVALID_POS"]):
                raise ValueError("Invalid storing position.")
            logger.warning("Delete failed.")


    def delete_all (self):
        """
        Deletes  all FP in memory.

        @return True if everything went right.
        @raises ValueError if DB was already empty.
        """
        logger.debug("Delete_all started.")
        response_packet = self.generic_Command(0x00,"DELETE_ALL")

        if(response_packet.response == 0x30):
            logger.debug("Delete_all ended.")
            return True

        elif(response_packet.response == 0x31):
            if(response_packet.parameter == response_packet.error_response_dict["NACK_DB_IS_EMPTY"]):
                raise ValueError("DB IS ALREADY EMPTY.")
            logger.debug("Delete_all failed.")


    def enroll(self, turn):
        """
        Issues the correct enroll command, based on the @turn
        parameter
        @param turn the correct enroll_request.
        @return True if everything was alright or False if wrong turn variable.
        @raises ValueError if Enrol_Failed, Poor_Quality_Fingeprint or Duplicated_Fingerprint.
        """
        logger.debug("Enroll #%s started." % str(turn))

        if (turn==1):
            response_packet = self.generic_Command(0x00,"ENROLL1")

            if(response_packet.response == 0x30):
                logger.debug("Enroll #%s ended." % str(turn))
                return True

            elif(response_packet.response == 0x31):
                logger.debug("Enroll #%s failed." % str(turn))

                if(response_packet.parameter == response_packet.error_response_dict["NACK_ENROLL_FAILED"]):
                    raise ValueError("Enroll Failed")
                elif(response_packet.parameter == response_packet.error_response_dict["NACK_BAD_FINGER"]):
                    raise ValueError("The fingerprint was poorly placed.")
                logger.debug("Enroll failed.")

        elif(turn == 2):
            response_packet = self.generic_Command(0x00,"ENROLL2")
            #response_packet.response_print()
    
            if(response_packet.response == 0x30):
                logger.debug("Enroll #%s ended." % str(turn))
                return True
            elif(response_packet.response == 0x31):
                logger.debug("Enroll #%s failed." % str(turn))

                if(response_packet.parameter == response_packet.error_response_dict["NACK_ENROLL_FAILED"]):
                    raise ValueError("Enroll Failed")
                elif(response_packet.parameter == response_packet.error_response_dict["NACK_BAD_FINGER"]):
                    raise ValueError("The fingerprint was poorly placed.")
                logger.debug("Enroll failed.")
    
        elif(turn == 3):
            response_packet = self.generic_Command(0x00,"ENROLL3")
            #response_packet.response_print()

            if(response_packet.response == 0x30):
                logger.debug("Enroll #%s ended." % str(turn))
                return True
    
            elif(response_packet.response == 0x31):
                logger.debug("Enroll #%s failed." % str(turn))

                if(response_packet.parameter == response_packet.error_response_dict["NACK_ENROLL_FAILED"]):
                    raise ValueError("Enroll Failed")
                elif(response_packet.parameter == response_packet.error_response_dict["NACK_BAD_FINGER"]):
                    raise ValueError("The fingerprint was poorly placed.")
                elif( 0 <= response_packet.parameter < 3000):
                    raise ValueError("DuplicatedID.")
                logger.debug("Enroll failed.")

        else:
            raise ValueError("Invalid turn variable.")

        return False 

    def get_Next_Empty_Space(self):
        """
        Searches for the next free space in the scanner, if
        there is none, returns -1
        
        @return the position of the next free space in the scanner or -1
        @raises ValueError if Database is full.
        """
        logging.debug("Get_Next_Empty_Space started.")
        for i in range(0,3000):
            if(self.check_Enrolled(i)):
                logging.debug("Get_Next_Empty_Space ended.")
                return i
            
        raise ValueError("Database is full, no empty spaces.")


    def enrollUser(self):
        """
        Handles the correct way to enroll a user.

        @return True if everything went accordingly.
        @raises ValueError if DB_full, Enroll_Failed, Fingerprint Poorly placed or duplicated ID.
        """
        logging.debug("Enroll_User started.")
        n = self.get_Next_Empty_Space() 
        self.Enroll_Start(n)
        
        for i in range(1,4):
            self.set_Led()
            while(self.is_Press_Finger()>0): 
                pass  
            self.CaptureFinger_Enroll() 
            self.off_Led()
            self.enroll(i)
            time.sleep(1)
        logging.debug("Enroll_User ended.")

        return True

    def enrollWithoutSaving(self):
        """
        Handles the correct way to enroll a user.

        @return True if everything went accordingly.
        @raises ValueError if DB_full, Enroll_Failed, Fingerprint Poorly placed or duplicated ID.
        """
        logging.debug("enrollUserWithoutSaving started.")

        self.Enroll_Start(-1)
        
        for i in range(1,4):
            self.set_Led()
            print("Put finger on scanner.")
            while(self.is_Press_Finger()>0): 
                pass  
            self.CaptureFinger_Enroll() 
            self.off_Led()
            response = self.enroll(i)
            time.sleep(1)
    
        if(response):
            data_packet = packets.data_packet(self.readPacket(504))

        logging.debug("enrollUserWithoutSaving ended.")

        return data_packet

    def Identify(self):
        """
        Tries to identify a fingerprint.
       
        @return Identified ID or False if none was found.
        @raises ValueError if database is empty. 
        """
        logging.debug("Identify started.")
        response_packet = self.generic_Command(0x00,"IDENTIFY")

        if(response_packet.response == 0x30):
            logging.debug("Identify ended.")
            return response_packet.parameter
        
        elif(response_packet.response == 0x31):

            if(response_packet.parameter == response_packet.error_response_dict["NACK_DB_IS_EMPTY"]):
                raise ValueError("Database is empty, unable to identify fp.")
            elif(response_packet.parameter == response_packet.error_response_dict["NACK_IDENTIFY_FAILED"]):
                logging.debug("Identify ended.")
                return False
            logging.warning("Identify failed.")
        

    def IdentifyUser(self):
        """
        Handles the correct way of calling Identify()

        @return the position where the user has been stored.
        @raises ValueError if DB is empty.
        """
        logging.debug("IdentifyUser started.")
        self.set_Led()
        print("Coloque o dedo para Identificacao")
        while(self.is_Press_Finger()>0): 
            pass 
        self.CaptureFinger_Identification()
        #self.off_Led()
        user_id = self.Identify()
        logging.debug("IdentifyUser ended.")

        return user_id

    # TO-DO,  IMPLEMENTATION TO GET OUT FROM STAND-BY MODE!
    def EnterStandbyMode(self):
        """
        Enter low power consumption mode.
        @return True if everything went alright.
        """
        logging.debug("EnterStandByMode started.")

        # to exit standby mode SEND 0x00 first and then wait 20ms to wake up and send other command
        response = self.generic_Command(0x00,"STANDBY_MODE")
        if(response.parameter == 0x30):
            logging.debug("EnterStandByMode ended.")
            return True
        else:
            raise ValueError("Failed to enter StandBy mode")

    def data_generic_Packet(self,param,command_Name):
        """
        Writes a data packet and handles it's possibles exceptions
        @return data_packet if evertything went alright
        @raises ValueError if  poor finger quality, invalid position or positionn not being used.
        """
        logging.debug("Generic_data_packet started.")

        cmd_packet = packets.command_packet(param, command_Name)
        self.writePacket(cmd_packet)
        response_packet = packets.response_packet(self.readPacket(12))
        if (response_packet.response == 0x30):
            logging.debug("Generic_data_packet ended.")
            data_packet = packets.data_packet(self.readPacket(504))
            return data_packet
        elif(response_packet.response == 0x31):
            if(response_packet.parameter == response_packet.error_response_dict["NACK_BAD_FINGER"]):
                raise ValueError("The fingerprint was poorly placed.")
            if(response_packet.parameter == response_packet.error_response_dict["NACK_INVALID_POS"]):
                raise ValueError("This position is not valid.")
            if(response_packet.parameter == response_packet.error_response_dict["NACK_IS_NOT_USED"]):
                raise ValueError ("This position is not being used")
                    
    def make_Template(self):
        """
        Requests fingerprint to user and makes a template
        but does not store it in memory.

        @return response if everything went alright.
        """
        logging.debug("Make_Template started.")
        self.set_Led()
        print("Coloque o dedo para criar template")
        while(self.is_Press_Finger()>0):
            pass 
        self.CaptureFinger_Identification()
        self.off_Led()
        time.sleep(2)
        response = self.data_generic_Packet(0x00,"MAKE_TEMPLATE")
        logging.debug("Make_Template ended.")
        return response

    def get_Template(self,id):
        """
        Requests template of given id.

        @parameter id a valid id of fp.
        @return data packet, containing the template of the finger.
        """
        logging.debug("Get_Template started.")
        data_packet = self.data_generic_Packet(id,"GET_TEMPLATE")
        logging.debug("Get_Template ended.")        
        return data_packet

    # To set a template even_though it's repeated, take the id parameter and "or-it" with 0xFFFF0000 (id = id|0xFFFF0000)
    def setTemplate(self,id,data):
        """
        Sets the template to a position in local memory.

        @parameter id the position to be stores. data the data PACKET (already mounted) with the fp.
        @return True if everything was alright.
        """
        logging.debug("Set_Template started.")
        response = self.generic_Command(id ,"SET_TEMPLATE")
        self.writeData(data)
        response_packet = packets.response_packet(self.readPacket(12))
        logging.debug("Set_Template ended.")        
        return True
