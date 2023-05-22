
from netsquid.components.qprogram import QuantumProgram
from netsquid.protocols import NodeProtocol
from netsquid.components.instructions import INSTR_CNOT,INSTR_H,INSTR_Z,INSTR_X,INSTR_MEASURE,INSTR_MEASURE_BELL
from netsquid.qubits import measure , reduced_dm, create_qubits,operate,gmeasure,assign_qstate
import numpy as np
from netsquid.qubits.operators import X,H,CNOT,Z
from random import randint
import time
import math
import netsquid as ns

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb, AssignStatesBydm,MeasureProb,add_it_count


key_len = 5

class TP_SenderTeleport(QuantumProgram):
    
    def __init__(self , idx):
        super().__init__()
        self.idx = idx
        
        
    def program(self):    
        self.apply(INSTR_CNOT, [0, 1])
        self.apply(INSTR_H, 0) 
            
        self.apply(INSTR_MEASURE,qubit_indices=0, output_key='0',physical=True) 
        self.apply(INSTR_MEASURE,qubit_indices=1, output_key='1',physical=True) 

        yield self.run(parallel=False)



class TP_ResetTeleport(QuantumProgram):
    
    def __init__(self  , res):
        super().__init__()
        self.res = res
        
    def program(self):
        if self.res[0] == 1:
            self.apply(INSTR_Z, 0)
        if self.res[1] == 1:
            self.apply(INSTR_X, 0)


        yield self.run(parallel=False)


class TP_ResetQubit(QuantumProgram):
    
    def __init__(self , idx, retry = False):
        super().__init__()
        self.idx = idx
        self.retry = retry
        
    def program(self):

        self.apply(INSTR_CNOT, [0, 1])
        self.apply(INSTR_MEASURE,qubit_indices=1, output_key='2',physical=True) 

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

        self.key = [randint(0,1) for i in range(key_len)]

        
    def run(self):
        self.send_qbit()
        mem_flip = False


        for i in range(key_len):
      
            start = time.time()
            count = 0

            qk_bit = create_qubits(1)
            a = .6
            b = .4
            if self.key[i] == 1:
                a ,b = b , a

            qk_bit = AssignStatesBydm([qk_bit] , [np.array([[a,1],[1,b]])])[0]
            self.processor.put(qk_bit ,  2 * key_len)

            myTP_SenderTeleport=TP_SenderTeleport(i)
            if mem_flip:
                self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[2* key_len , i])
            else:
                self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[2 * key_len , i + key_len])

            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            yield self.await_program(processor=self.processor)


            if True:

                self.measureRes = [myTP_SenderTeleport.output['0'][0] , myTP_SenderTeleport.output['1'][0]]
                # print('send res:' , self.measureRes , i)
                # time.sleep(.1)
                self.node.ports[self.portNameCS1].tx_output(self.measureRes)
                # print('before reset teleport i:',i , 'mem_flip:' , mem_flip)
                # self.print_qubits( i , count)
                for j in range(i +1 , key_len ):
                    myTP_ResetTeleport=TP_ResetTeleport(self.measureRes)
                    self.processor.execute_program(myTP_ResetTeleport,qubit_mapping=[j + key_len])
                    self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                    yield self.await_program(processor=self.processor)
                i = i+1

                # time.sleep(.1)
                if i < key_len:
                    self.prepare_reset_qubit(i)

                    myTP_ResetQubit=TP_ResetQubit(i)
                    self.processor.execute_program(myTP_ResetQubit,qubit_mapping=[i , i + key_len])
                    self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                    yield self.await_program(processor=self.processor)
                    meas = myTP_ResetQubit.output['2'][0]
                    count +=1
                    # print('meas at attmpt: ' , count , meas)

                    flip = True    
                    p , q = MeasureProb(self.processor.peek(i))

                    while meas != 0 :


                        if meas == 1:
                            if flip:
                                operate(self.processor.peek(i), X)
                            else:
                                operate(self.processor.peek(i + key_len), X)
                        self.prepare_reset_qubit(i ,not flip , count)


                        myTP_ResetQubit=TP_ResetQubit(i, flip)
                        if flip:
                            self.processor.execute_program(myTP_ResetQubit,qubit_mapping=[i + key_len, i])
                        else:
                            self.processor.execute_program(myTP_ResetQubit,qubit_mapping=[i, i + key_len])

                        self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                        yield self.await_program(processor=self.processor)
                        meas = myTP_ResetQubit.output['2'][0]
                        p , q = MeasureProb(self.processor.peek(i))
                        if flip:
                            p , q = MeasureProb(self.processor.peek(i + key_len))
                        flip = not flip

                        count = count +1

                    if meas == 1:
                        if flip:
                            operate(self.processor.peek(i), X)
                        else:
                            operate(self.processor.peek(i + key_len), X)
                    mem_flip = flip

                i = i-1


        # time.sleep(2)
        print('sent key ' , self.key)

    
    
    def print_qubits(self , i , count):
        print('----------- remaining qbits ------------ i: ' , i , 'count:' , count)
        for j in range(0,key_len):
            try:
                print(j , ':' , )
                MeasureByProb(self.processor.peek(j + key_len) , do_print=True)
            except:
                print('exception')
        print('other: 2 * key_len ')
        MeasureByProb(self.processor.peek(2 * key_len) , do_print=True)
        print('other in i  : ' , i)

        MeasureByProb(self.processor.peek(i ) , do_print=True)
        print('------------------------------------')
    def gen_qubits(self):
        qubits=create_qubits(key_len + 1)
        operate(qubits[0] , H)


        for i in range(1 , key_len + 1 ):
            operate([qubits[0] , qubits[i]] , CNOT)

        return qubits
    def prepare_reset_qubit(self  , i , for_next = True , num_try = 1):
        
        alpha, beta = MeasureProb(self.processor.peek(i +  (key_len if for_next else 0)))

        b = alpha 
        a = beta 

        b,a = 0.5 / a , 0.5/b
        

        qubit=create_qubits(1)

        qubit = AssignStatesBydm([qubit] , [np.array([[a,1],[1,b]])])[0]

        if for_next:
            self.processor.put(qubit , i)
        else:
            self.processor.put(qubit , i + key_len)

    
    def reset_processor_mem(self):
        for i in range(2*key_len):
            self.processor.pop(0)
        self.processor.put(self.cqubits + self.qubits)

    def send_qbit(self):
        qubit = self.processor.pop(2* key_len )
        self.node.ports[self.portNameQS1].tx_output(qubit)

        # qubit = self.processor.pop(2* key_len )
        # self.node.ports[self.portNameQS2].tx_output(qubit)




        
        