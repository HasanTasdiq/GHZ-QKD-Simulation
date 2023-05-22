from netsquid.protocols import NodeProtocol
from netsquid.components.qprogram import QuantumProgram

#from netsquid.qubits.qformalism import *
from netsquid.qubits.qstate import QState
from netsquid.qubits import set_qstate_formalism, QFormalism
from netsquid.components.instructions import INSTR_X,INSTR_Z,INSTR_H
from netsquid.qubits import measure , reduced_dm,fidelity,outerprod,ketstates
import netsquid as ns
import numpy as np

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb,MeasureProb,AssignStatesBydm

from Alice import key_len



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
        
        yield self.run(parallel=False)
        



        
class QuantumTeleportationReceiver(NodeProtocol):
    
    def __init__(self,node,processor,portNames=["portC_Receiver"],bellState=1,delay=0): 
        super().__init__()
        self.node=node
        self.processor=processor
        self.bellState=bellState


        self.portNameCR1=portNames[0]
        self.portNameQR1=portNames[1]

        self.receivedQubit=None
        self.delay=delay

        set_qstate_formalism(QFormalism.DM)
        
    def run(self):

        key = []
        port = self.node.ports[self.portNameQR1]

        
        yield self.await_port_input(port)
        received_qubit = port.rx_input().items

        self.processor.put(received_qubit)

        self.prevRes = []

        self.prevAlpha = 1
        self.prevBeta = 1

        for i in range(key_len):
        
            port=self.node.ports[self.portNameCR1]
            yield self.await_port_input(port)
            res=port.rx_input().items


            while res[0] == 'check':
                print('-----------receiver qbit after reset------------ i: ' , i)
                MeasureByProb(self.receivedQubit , do_print=True)
                print('------------------------------------')
                yield self.await_port_input(port)
                res=port.rx_input().items

            self.receivedQubit=self.processor.peek(0)[0]


            if self.delay>0:
                yield self.await_timer(duration=self.delay)


            myTP_ReceiverAdjust=TP_ReceiverAdjust(self.bellState,res)
            self.processor.execute_program(myTP_ReceiverAdjust,qubit_mapping=[0])
            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            yield self.await_program(processor=self.processor)

            self.receivedQubit=self.processor.peek(0)[0]


            key.append(MeasureByProb(self.receivedQubit , do_print=False))

            self.prevRes = res


        self.key = key
        print('received ' , key)



    
    def extractRes(self , qubit , res):
        
        prob_0 , prob_1 = MeasureProb(qubit)
        alpha = prob_0 
        beta = prob_1
        z = 0
        if len(self.prevRes) > 0 and  self.prevRes[0] == 1:
            z = 1
        if len(self.prevRes) > 0 and self.prevRes[0]:
            if res[1] == 0:
                alpha = prob_0/self.prevAlpha
                beta = prob_1 / self.prevBeta
            elif res[1] == 1:
                alpha = prob_0/self.prevBeta
                beta = prob_1 / self.prevAlpha
        
        if len(self.prevRes) > 0 and self.prevRes[1]:
            if res[1] == 0:
                alpha = prob_0/self.prevBeta
                beta = prob_1 / self.prevAlpha
            elif res[1] == 1:
                alpha = prob_0/self.prevAlpha
                beta = prob_1 / self.prevBeta
        
        
        if len(self.prevRes) > 0 and self.prevRes[0] == 1 and self.prevRes[1] == 0   and res[1] == 1:
            alpha = -alpha

        if len(self.prevRes) > 0 and self.prevRes[0] == 1 and self.prevRes[1] == 1:
            if res[1] == 0:
                alpha = -alpha
            elif res[1] == 1:
                beta = -beta    


        self.prevAlpha = alpha
        self.prevBeta = beta

        mes = 1
        
        if alpha > beta:
            mes = 0

        return mes