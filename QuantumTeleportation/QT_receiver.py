from netsquid.protocols import NodeProtocol
from netsquid.components.qprogram import QuantumProgram

#from netsquid.qubits.qformalism import *
from netsquid.qubits.qstate import QState
from netsquid.qubits import set_qstate_formalism, QFormalism
from netsquid.components.instructions import INSTR_X,INSTR_Z,INSTR_H
from netsquid.qubits import measure , reduced_dm


import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb

from QT_sender import key_len



class TP_ReceiverAdjust(QuantumProgram):
    
    def __init__(self,bellState,adjBase):
        super().__init__()
        self.bellState=bellState
        self.adjBase=adjBase
        
        
    def program(self):

        if self.adjBase[0]==1:
            self.apply(INSTR_Z, 0)  
            
        if self.adjBase[1]==1:
            self.apply(INSTR_X, 0)

        # if self.bellState == 1:
        #     if self.adjBase[0]==1:
        #         self.apply(INSTR_Z, 0)  
            
        #     if self.adjBase[1]==1:
        #         self.apply(INSTR_X, 0)

        # elif self.bellState == 3:
        #     if self.adjBase[0]==1:
        #         self.apply(INSTR_Z, 0)  
            
        #     if self.adjBase[1]==0:
        #         self.apply(INSTR_X, 0)

        # else:
        #     print("R undefined case in TP_ReceiverAdjust")
        
        # self.apply(INSTR_H , 0)                
        
        yield self.run(parallel=False)


class TP_ReceiverReset(QuantumProgram):
    
    def __init__(self,bellState,adjBase):
        super().__init__()
        self.bellState=bellState
        self.adjBase=adjBase
        
        
    def program(self):

        if self.adjBase[1]==1:
            self.apply(INSTR_X, 0)

        if self.adjBase[0]==1:
            self.apply(INSTR_Z, 0)  
            


        # if self.bellState == 1:

        #     if self.adjBase[1]==1:
        #         self.apply(INSTR_X, 0)
        #     if self.adjBase[0]==1:
        #         self.apply(INSTR_Z, 0)  
            


        # elif self.bellState == 3:
        #     if self.adjBase[1]==0:
        #         self.apply(INSTR_X, 0)

        #     if self.adjBase[0]==1:
        #         self.apply(INSTR_Z, 0)  
            


        # else:
        #     print("R undefined case in TP_ReceiverAdjust")
        
        # self.apply(INSTR_H , 0)                
        
        yield self.run(parallel=False)
        



        
class QuantumTeleportationReceiver(NodeProtocol):
    
    def __init__(self,node,processor,EPR_2,portNames=["portC_Receiver"],bellState=1,delay=0): 
        super().__init__()
        self.node=node
        self.processor=processor
        self.bellState=bellState

        self.resultQubit=EPR_2
        self.portNameCR1=portNames[0]
        self.receivedQubit=None
        self.processor.put(self.resultQubit)
        self.delay=delay

        set_qstate_formalism(QFormalism.DM)
        
    def run(self):

        key = []

        for i in range(key_len):
        
            port=self.node.ports[self.portNameCR1]
            yield self.await_port_input(port)
            res=port.rx_input().items
            print("R get results:", res)
            

            # wait for delay ns
            if self.delay>0:
                yield self.await_timer(duration=self.delay)


            # edit EPR2 according to res
            myTP_ReceiverAdjust=TP_ReceiverAdjust(self.bellState,res)
            self.processor.execute_program(myTP_ReceiverAdjust,qubit_mapping=[0])
            #self.processor.set_program_done_callback(self.show_state,once=True) # see qstate
            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            yield self.await_program(processor=self.processor)

            self.receivedQubit=self.processor.peek(0)[0]

            # print(measure(self.receivedQubit))
            # print(MeasureByProb(self.receivedQubit))
            key.append(MeasureByProb(self.receivedQubit))



            myTP_ReceiverReset=TP_ReceiverReset(self.bellState,res)
            self.processor.execute_program(myTP_ReceiverReset,qubit_mapping=[0])
            #self.processor.set_program_done_callback(self.show_state,once=True) # see qstate
            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            yield self.await_program(processor=self.processor)

        print('received key: '  , key)


    def show_state(self):
        set_qstate_formalism(QFormalism.DM)
        tmp=self.processor.pop(0)[0]
        print("R final state:",tmp.qstate.dm)