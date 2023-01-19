
import sys
from croblink import *
from math import *
import xml.etree.ElementTree as ET
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

CELLROWS=7
CELLCOLS=14

class MyRob(CRobLinkAngs):
    def __init__(self, rob_name, rob_id, angles, host):
        CRobLinkAngs.__init__(self, rob_name, rob_id, angles, host)

    def setMap(self, labMap):
        self.labMap = labMap


    def run(self):
        if self.status != 0:
            print("Connection refused or error")
            quit()

        state = 'stop'
        stopped_state = 'run'

        while True:
            self.readSensors()

            if self.measures.endLed:
                print(self.rob_name + " exiting")
                quit()

            if state == 'stop' and self.measures.start:
                state = stopped_state

            if state != 'stop' and self.measures.stop:
                stopped_state = state
                state = 'stop'

            if state == 'run':
                if self.measures.visitingLed==True:
                    state='wait'
                if self.measures.ground==0:
                    self.setVisitingLed(True);
                self.wander()
            elif state=='wait':
                self.setReturningLed(True)
                if self.measures.visitingLed==True:
                    self.setVisitingLed(False)
                if self.measures.returningLed==True:
                    state='return'
                self.driveMotors(0.0,0.0)
            elif state=='return':
                if self.measures.visitingLed==True:
                    self.setVisitingLed(False)
                if self.measures.returningLed==True:
                    self.setReturningLed(False)
                self.wander()
            

    def wander(self):
        center_id = 0
        left_id = 1
        right_id = 2
        back_id = 3


        wheel_speed = 0.15
        print(self.measures.lineSensor)
        #should change this to look like fuzz but can't be bothered its 5:35 am 
       
        line = [x == '1' for x in self.measures.lineSensor]
        line = [int(x) for x in self.measures.lineSensor]
        line = np.array(line, dtype=float)
        #find the difference betweend two sides
        operationline=line
        operationline=(operationline[::-1][:3]-operationline[:3])
 
        input=operationline.sum()
        print(operationline)
        print(input)
        if input< 0:
            line[-3:] = [0,0,0]
        elif input>0:
            line[0:3] = [0,0,0]

        #left
        if line[0] and line[1]:
            print("sharp left")
            self.driveMotors(-wheel_speed,+wheel_speed)
        elif line[1]:
            print("slow left")
            self.driveMotors(0,+wheel_speed)
        #right
        elif line[-1] and line[-2]:
            print("fast right")
            self.driveMotors(+wheel_speed,-wheel_speed)
        elif line[-2]:
            print("slow rgiht")
            self.driveMotors(+wheel_speed,0)
            self.driveMotors(+0.15,0)
        #left
        elif not line[4]:
            print("slow left 2")

            self.driveMotors(0,+wheel_speed)
        #right
        elif not line[2]:
            print("slow right 2")

            self.driveMotors(+wheel_speed,0)
        #fwd
        else:
            print("forwad")
            self.driveMotors(wheel_speed,wheel_speed)


class Map():
    def __init__(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        
        self.labMap = [[' '] * (CELLCOLS*2-1) for i in range(CELLROWS*2-1) ]
        i=1
        for child in root.iter('Row'):
           line=child.attrib['Pattern']
           row =int(child.attrib['Pos'])
           if row % 2 == 0:  # this line defines vertical lines
               for c in range(len(line)):
                   if (c+1) % 3 == 0:
                       if line[c] == '|':
                           self.labMap[row][(c+1)//3*2-1]='|'
                       else:
                           None
           else:  # this line defines horizontal lines
               for c in range(len(line)):
                   if c % 3 == 0:
                       if line[c] == '-':
                           self.labMap[row][c//3*2]='-'
                       else:
                           None
               
           i=i+1


rob_name = "pClient1"
host = "localhost"
pos = 1
mapc = None



if __name__ == '__main__':
    sys.stdout = open("debug.txt", "w")
    rob=MyRob(rob_name,pos,[0.0,60.0,-60.0,180.0],host)
    if mapc != None:
        rob.setMap(mapc.labMap)
    
    rob.run()
