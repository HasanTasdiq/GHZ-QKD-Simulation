
from netsquid.components.qprogram import QuantumProgram
from netsquid.protocols import NodeProtocol
from netsquid.components.instructions import INSTR_CNOT,INSTR_H,INSTR_MEASURE,INSTR_MEASURE_BELL
from netsquid.qubits import measure , reduced_dm, create_qubits,operate
import numpy as np
from netsquid.qubits.operators import X,H,CNOT

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb, AssignStatesBydm



class TP_SenderTeleport(QuantumProgram):
    
    def __init__(self):
        super().__init__()
        
    def program(self):
        # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='2',physical=True) # measure the origin state
        # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='2',physical=True) # measure the epr1
        self.apply(INSTR_MEASURE_BELL,qubit_indices=[2,1], output_key='2',physical=True) # measure the epr1
        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[0,1], output_key='3',physical=True) # measure the epr1
        
        # self.apply(INSTR_H, 0) 
        # self.apply(INSTR_CNOT, [0, 1])


        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[2,1], output_key='3',physical=True) # measure the epr1


        # self.apply(INSTR_CNOT, [2, 0])
        # self.apply(INSTR_H, 2) 


        # EPR-like        
        # self.apply(INSTR_CNOT, [0, 1])
        # self.apply(INSTR_H, 0) 
        
        # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='0',physical=True) # measure the origin state
        # self.apply(INSTR_MEASURE,qubit_indices=1, output_key='1',physical=True) # measure the epr1
        

        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[0,1], output_key='2',physical=True) # measure the epr1


        yield self.run(parallel=False)





class QuantumTeleportationSender(NodeProtocol):
    
    def __init__(self,node,processor,SendQubit,EPR_1,portNames=["portC_Sender"]): 
        super().__init__()
        self.node=node
        self.processor=processor
        self.SendQubit=SendQubit
        self.EPR_1=EPR_1
        self.measureRes=None
        self.portNameCS1=portNames[0]

        sendQubit2 , ddd=create_qubits(2)
        sendQubit2 = AssignStatesBydm([sendQubit2] , [np.array([[1,0.88],[0.88,0]])])[0]
        SendQubit = AssignStatesBydm([SendQubit] , [np.array([[1,0.88],[0.88,0]])])[0]
        self.sendQubit2 = sendQubit2

        operate(SendQubit, H)
        operate([SendQubit, sendQubit2], CNOT)

        print('ent send1 ' , MeasureByProb(self.SendQubit))
        print('ent send2 ' , MeasureByProb(self.sendQubit2))

        self.processor.put([SendQubit,EPR_1, sendQubit2])
        
        
        
    def run(self):
        
        # Entangle the two qubits and measure
        # print('send 1 ', measure(self.SendQubit))
        # print('send 2 ' , measure(self.SendQubit))
        myTP_SenderTeleport=TP_SenderTeleport()
        self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[0,1,2])
        self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
        
        yield self.await_program(processor=self.processor)
        # self.measureRes=[myTP_SenderTeleport.output['0'][0],myTP_SenderTeleport.output['1'][0]]
        # print('before bsm ' , self.measureRes)
        self.measureRes = [0,0]

        output2 = myTP_SenderTeleport.output['2'][0]
        print('out2 ' , output2)
        # operate(oriQubit, H) # init qubit

        # if output2 == 1:
        #     self.measureRes = [0,1]
        # elif output2 == 3:
        #     self.measureRes = [1,0]
        # elif output2 == 2:
        #     self.measureRes = [1,1]




        # print('out3 ' , myTP_SenderTeleport.output['3'][0])
        # Send results to Receiver
        self.node.ports[self.portNameCS1].tx_output(self.measureRes)

        print('from sender sendbit' , MeasureByProb(self.SendQubit))
        print('from sender epr1' , MeasureByProb(self.EPR_1))
        # print('from sender ori2' , MeasureByProb(self.sendQubit2))

        print('send 1 ', measure(self.SendQubit))

    # def run(self):
        
    #     # Entangle the two qubits and measure
    #     # print('send 1 ', measure(self.SendQubit))
    #     # print('send 2 ' , measure(self.SendQubit))
    #     myTP_SenderTeleport=TP_SenderTeleport()
    #     self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[0,1])
    #     self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
        
    #     yield self.await_program(processor=self.processor)
    #     self.measureRes=[myTP_SenderTeleport.output['0'][0],myTP_SenderTeleport.output['1'][0]]

    #     self.node.ports[self.portNameCS1].tx_output(self.measureRes)


        
        