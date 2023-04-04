
from netsquid.components.qprogram import QuantumProgram
from netsquid.protocols import NodeProtocol
from netsquid.components.instructions import INSTR_CNOT,INSTR_H,INSTR_MEASURE,INSTR_MEASURE_BELL
from netsquid.qubits import measure , reduced_dm, create_qubits,operate
import numpy as np
from netsquid.qubits.operators import X,H,CNOT
from random import randint

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb, AssignStatesBydm


key_len = 5

class TP_SenderTeleport(QuantumProgram):
    
    def __init__(self , idx):
        super().__init__()
        self.idx = idx
        
    def program(self):
        # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='2',physical=True) # measure the origin state
        # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='2',physical=True) # measure the epr1
        self.apply(INSTR_MEASURE_BELL,qubit_indices=[self.idx,self.idx + key_len], output_key='2',physical=True) # measure the epr1
        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[3,2], output_key='3',physical=True) # measure the epr1
        
        # self.apply(INSTR_H, 0) 
        # self.apply(INSTR_CNOT, [0, 1])


        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[2,1], output_key='3',physical=True) # measure the epr1


        # self.apply(INSTR_CNOT, [2, 0])
        # self.apply(INSTR_H, 2) 


        # EPR-like        
        # self.apply(INSTR_CNOT, [0, 1])
        # self.apply(INSTR_H, 0) 
        
        # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='0',physical=True) # measure the origin state
        # self.apply(INSTR_MEASURE,qubit_indices=2, output_key='1',physical=True) # measure the epr1
        

        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[0,1], output_key='2',physical=True) # measure the epr1


        yield self.run(parallel=False)





class QuantumTeleportationSender(NodeProtocol):
    
    def __init__(self,node,processor,qubits,portNames=["portC_Sender"]): 
        super().__init__()
        self.node=node
        self.processor=processor
        self.qubits=qubits
        self.measureRes=None
        self.portNameCS1=portNames[0]

        self.cqubits = create_qubits(key_len)

        self.processor.put(self.cqubits + self.qubits)

        self.key = [randint(0,1) for i in range(key_len)]
        print('------key------ ' , self.key)

        for i in range(key_len):
            self.qubits[i] = AssignStatesBydm([self.qubits[i]] , [np.array([[1 - self.key[i],0.88],[0.88,self.key[i]]])])[0]
        
        
        
    def run(self):

        for i in range(key_len):
        
            myTP_SenderTeleport=TP_SenderTeleport(i)
            self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=list(range(2*key_len)))
            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            
            yield self.await_program(processor=self.processor)
            self.measureRes = [0,0]

            output2 = myTP_SenderTeleport.output['2'][0]
            # print('out2 ' , output2)
            # operate(oriQubit, H) # init qubit

            if output2 == 1:
                self.measureRes = [0,1]
            elif output2 == 3:
                self.measureRes = [1,0]
            elif output2 == 2:
                self.measureRes = [1,1]
            print('sends res ' , self.measureRes)
            self.node.ports[self.portNameCS1].tx_output(self.measureRes)

            # print('from sender EPR0' , MeasureByProb(self.cqubits[i]))
            # print('from sender epr1' , MeasureByProb(self.EPR_1))



        
        