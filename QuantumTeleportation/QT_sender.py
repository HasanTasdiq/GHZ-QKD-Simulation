
from netsquid.components.qprogram import QuantumProgram
from netsquid.protocols import NodeProtocol
from netsquid.components.instructions import INSTR_CNOT,INSTR_H,INSTR_Z,INSTR_X,INSTR_MEASURE,INSTR_MEASURE_BELL
from netsquid.qubits import measure , reduced_dm, create_qubits,operate
import numpy as np
from netsquid.qubits.operators import X,H,CNOT
from random import randint
import time

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb, AssignStatesBydm,MeasureProb


key_len = 6

class TP_SenderTeleport(QuantumProgram):
    
    def __init__(self , idx):
        super().__init__()
        self.idx = idx
        
    def program(self):
        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[0,1], output_key='2',physical=True) # measure BSm



        # EPR-like       
         
        if self.idx %2 == 0:
            self.apply(INSTR_CNOT, [0, 1])
            self.apply(INSTR_H, 0) 
            
            self.apply(INSTR_MEASURE,qubit_indices=0, output_key='0',physical=True) # measure the origin state
            self.apply(INSTR_MEASURE,qubit_indices=1, output_key='1',physical=True) # measure the epr1
        else:
            self.apply(INSTR_CNOT, [0, 1])
            self.apply(INSTR_MEASURE,qubit_indices=1, output_key='2',physical=True) # measure the origin state
            # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='3',physical=True) # measure the origin state



        yield self.run(parallel=False)



class TP_ResetTeleport(QuantumProgram):
    
    def __init__(self  , res):
        super().__init__()
        self.res = res
        
    def program(self):
        # EPR-like       
        if self.res[0] == 1:
            self.apply(INSTR_Z, 0)
        if self.res[1] == 1:
            self.apply(INSTR_X, 0)


        yield self.run(parallel=False)




class QuantumTeleportationSender(NodeProtocol):
    
    def __init__(self,node,processor,portNames=["portC_Sender"]): 
        super().__init__()
        self.node=node
        self.processor=processor
        self.qubits=self.gen_qubits()
        self.measureRes=None
        self.portNameQS1='portQ_Sender'
        self.portNameQS2='portQ_Sender2'

        self.portNameCS1=portNames[0]
        self.portNameCS2=portNames[1]

        self.cqubits = create_qubits(key_len)



        self.processor.put(self.cqubits + self.qubits)
        # self.processor.put(self.qubits + self.cqubits)

        # self.key = [randint(0,1) for i in range(key_len)]
        self.key = [0,1,0,1 , 0 , 1]
        print('------key------ ' , self.key)

        
        p = .5
        q = .5
        for i in range(key_len):
            a = .9
            b = .1
            if self.key[i] == 1:
                a = .1
                b = .9

            self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[a,1],[1,b]])])[0]

            # if i % 2 == 1:
            #     operate(self.cqubits[i] , H)
            #     # self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[p,1],[1,q]])])[0]

            # p = a
            # q = b

            # if i %2 == 0:
            #     # operate(self.cqubits[i] , H)

            #     self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[1 - self.key[i],1],[1,self.key[i]]])])[0]
            # else:
            #     # operate(self.cqubits[i] , H)
            #     # self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[1 - self.key[i],1],[1,self.key[i]]])])[0]

            #     self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[.4,0.5],[0.5,.6]])])[0]
        
        
        
    def run(self):
        self.send_qbit()


        for i in range(key_len):


            start = time.time()

            print('cqubits[i] before program ' , i , MeasureProb(self.cqubits[i]))
        
            myTP_SenderTeleport=TP_SenderTeleport(i)
            # self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=list(range(2*key_len)))
            self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[i , i + key_len])
            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            
            yield self.await_program(processor=self.processor)


            if i %2 ==0:
                self.measureRes = [myTP_SenderTeleport.output['0'][0] , myTP_SenderTeleport.output['1'][0]]
                # self.measureRes = [0,0]

                # output2 = myTP_SenderTeleport.output['2'][0]

                # if output2 == 1:
                #     self.measureRes = [0,1]
                # elif output2 == 3:
                #     self.measureRes = [1,0]
                # elif output2 == 2:
                #     self.measureRes = [1,1]
                print('sends res ' , self.measureRes)
                self.node.ports[self.portNameCS1].tx_output(self.measureRes)
                

                for j in range(i , key_len ):
                    myTP_ResetTeleport=TP_ResetTeleport(self.measureRes)
                    self.processor.execute_program(myTP_ResetTeleport,qubit_mapping=[j + key_len])
                    self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                    yield self.await_program(processor=self.processor)
                self.prepare_reset_qubit(i+1)

            else:
                
                meas = myTP_SenderTeleport.output['2'][0]
                print('#@#@#@#@ measure output ' , meas)

                print('cqubits[i] ' , i , MeasureProb(self.cqubits[i]))
                # print('processor qubit i  ' , i , MeasureProb(self.processor.pop(i)))

                print('qubits[i] ' , i , MeasureProb(self.qubits[i]))
                print('qubits[i + 1] ' , i + 1 , MeasureProb(self.qubits[i+1]))
                while meas != 0 :
                    print('----------- remaining qbits in while ------------ i: ' , i)
                    for j in range(0,key_len):
                        MeasureByProb(self.qubits[j] , do_print=True)
                    print('------------------------------------')


                    myTP_SenderTeleport=TP_SenderTeleport(i)
                    operate(self.cqubits[i], X)
                    print('cqubits[i] in while loop after X ' , MeasureProb(self.cqubits[i]))

                    # self.qubits[i] = self.cqubits[i]
                    tmp_qbit = self.processor.peek(i)
                    self.prepare_reset_qubit(i)
                    self.processor.put(tmp_qbit , key_len + i)

                    self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[i , i + key_len])
                    self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                    yield self.await_program(processor=self.processor)
                    meas = myTP_SenderTeleport.output['2'][0]
                    print('#@#@#@#@ measure output in while loop' , meas)
                    # break



            # yield self.await_program(processor=self.processor)

            
            print('----------- remaining qbits ------------ i: ' , i)
            for j in range(0,key_len):
                try:
                    print(j , ':' , )
                    MeasureByProb(self.qubits[j] , do_print=True)
                except:
                    print('exception')
            print('------------------------------------')

            # self.node.ports[self.portNameCS2].tx_output(self.measureRes)


            # print('from sender EPR0' , MeasureByProb(self.cqubits[i]))
            # print('from sender epr1' , MeasureByProb(self.EPR_1))
    
    def gen_qubits(self):
        qubits=create_qubits(key_len + 1)
        operate(qubits[0] , H)

        # for i in range(0 , n_qubits ):
        #     operate([qubits[i] , qubits[i+1]] , CNOT)

        for i in range(1 , key_len + 1 ):
            operate([qubits[0] , qubits[i]] , CNOT)
        
        return qubits
    def prepare_reset_qubit(self  , i):
        if i + 1 >= len(self.key):
            return
        b , a = MeasureProb(self.processor.peek(i))
        print('prepare reset bit ', a, b)
        # if self.key[i] == 0:
        #     a = .1
        #     b = .9
        
        # if self.measureRes[0] == 0 and self.measureRes[1] == 0:
        #     t = a
        #     a = b
        #     b = t
        # if self.measureRes[0] == 1 and self.measureRes[1] == 0:
        #     t = a
        #     a = a + b
        #     b = -t
        
        # if self.measureRes[0] == 1 and self.measureRes[1] == 1:
        #     # t = a
            
        #     b = b + a + a
        #     a = -a

        qubit=create_qubits(1)
        self.cqubits[i] = AssignStatesBydm([qubit] , [np.array([[a,1],[1,b]])])[0]
        print("***********************************")
        self.processor.put(qubit , i)
        # print('processor qubit i  ' , i , MeasureProb(self.processor.pop(i)))
        print('self.cqubits[i] = AssignStatesBydm '  , i  , MeasureProb(self.cqubits[i]))
        # print('self.qubits[i] = AssignStatesBydm '  , i  , MeasureProb(self.qubits[i]))
        # self.reset_processor_mem()

    
    def reset_processor_mem(self):
        for i in range(2*key_len):
            self.processor.pop(0)
        self.processor.put(self.cqubits + self.qubits)

    def send_qbit(self):
        qubit = self.processor.pop(2* key_len )
        self.node.ports[self.portNameQS1].tx_output(qubit)

        # qubit = self.processor.pop(2* key_len )
        # self.node.ports[self.portNameQS2].tx_output(qubit)




        
        