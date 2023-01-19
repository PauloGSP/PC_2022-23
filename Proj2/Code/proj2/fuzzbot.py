import sys
from croblink import *
from math import *
import xml.etree.ElementTree as ET
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

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
        #create line as int instead of char
        line = [int(x) for x in self.measures.lineSensor]
        line = np.array(line, dtype=float)
        #find the difference betweend two sides
        line=(line[::-1][:3]-line[:3])
        c=4
        #give them the values
        #a diferença das listas pode ser  
        # [ 1 1 1] =7
        # [1 1 0] = 6
        #  [1 0 1] =5
        # [1 0 0] =4
        # [0 1 1] =3
        #  [0 1 0]= 2
        #  [ 0 0 1] =1
        # há 7 possibilidades
        #consoante o numero e a posiçao dos 1 (à esquerda é maior)
        #  mais rapido ele deve fazer a ação
        for i in range(len(line)):
            line[i]*=c
            c-=c/2

        input=line.sum()+7
        # to define the number of 1's to the left and right of the center point
        # we can define an antecedent like with this universe [-3 -2 -1  0  1  2  3]
        # negative means left positive means right

        #definir defnir o quao muito ele vai rodar input e outputs
        # 0-15
        line_position = ctrl.Antecedent(np.arange(0,15), 'line_position')
        movement = ctrl.Consequent(np.arange(-15,16), 'movement')        
        #memberships
        line_position['left'] = fuzz.trimf(line_position.universe, [0, 0, 7])
        line_position['center']= fuzz.trimf(line_position.universe, [7, 7, 7])
        line_position['right'] = fuzz.trimf(line_position.universe, [7, 15 , 15])
        #aqui basicamente dizemos pra q lado temos q mover e o quao muito 
        movement['left'] = fuzz.trimf(movement.universe, [-15, -15, 0])
        movement['center'] = fuzz.trimf(movement.universe, [0,0,0])
        movement['right'] = fuzz.trimf(movement.universe, [0, 15, 15])
                

        # Define fuzzy rules

        rule1 = ctrl.Rule(line_position['left'], movement['left'])
        rule2 = ctrl.Rule(line_position['center'], movement['center'])
        rule3 = ctrl.Rule(line_position['right'], movement['right'])

        # control system
        line_follower_control = ctrl.ControlSystem([rule1, rule2, rule3])
        line_follower = ctrl.ControlSystemSimulation(line_follower_control)

        # compute the output and send input
        line_follower.input['line_position'] = input
        line_follower.compute()
      

        # Use the computed output to control the robot's movements rounded to 2 decimal cases 
        speed = round(line_follower.output['movement'],2)
        #movement should come at -10 10 max so i want the robot to move at the max with 0.25 speed so 
        wheel_speed = 0.15  
        #0.2=2800
        #0.1=2700
        #0.15=3200


        #left
        if speed<0:
            speed=(speed/10)*-wheel_speed
            print("left" + str(speed))

            self.driveMotors(-speed,+speed)
        elif speed>0:
            speed=(speed/10)*wheel_speed
            print("right" + str(speed))
            self.driveMotors(+speed,-speed)

        else:
            print("fwd" + str(speed))
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
