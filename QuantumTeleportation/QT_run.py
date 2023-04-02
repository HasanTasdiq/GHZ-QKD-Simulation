import numpy as np
import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.protocols import NodeProtocol
from netsquid.qubits.operators import X,H,CNOT
from netsquid.components.qprocessor import QuantumProcessor,PhysicalInstruction

from netsquid.components.qchannel import QuantumChannel
from netsquid.components.cchannel import ClassicalChannel
from netsquid.components import QSource,Clock
from netsquid.components.qsource import SourceStatus
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.components.models.delaymodels import FibreDelayModel
from netsquid.components.instructions import  INSTR_X,INSTR_Z,INSTR_CNOT,INSTR_H,INSTR_MEASURE,INSTR_MEASURE_BELL
from netsquid.qubits.qubitapi import create_qubits,operate
from netsquid.qubits import measure , reduced_dm,assign_qstate,set_qstate_formalism,QFormalism,gmeasure


from random import randint

from QT_sender import QuantumTeleportationSender
from QT_receiver import QuantumTeleportationReceiver

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import AssignStatesBydm , MeasureByProb

def run_Teleport_sim(runtimes=1,fibre_len=10**-9,memNoiseMmodel=None,processorNoiseModel=None,delay=0
               ,loss_init=0,loss_len=0,QChV=3*10**-4,CChV=3*10**-4):
    
    
    
    for i in range(runtimes): 
        
        ns.sim_reset()

        # nodes====================================================================

        nodeSender   = Node("SenderNode"    , port_names=["portC_Sender"])
        nodeReceiver = Node("ReceiverNode"  , port_names=["portC_Receiver"])

        # processors===============================================================
        processorSender=QuantumProcessor("processorSender", num_positions=10,
            mem_noise_models=memNoiseMmodel, phys_instructions=[
            PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_CNOT,duration=10,quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_MEASURE, duration=10,quantum_noise_model=processorNoiseModel, parallel=False),
            PhysicalInstruction(INSTR_MEASURE_BELL, duration=10,quantum_noise_model=processorNoiseModel, parallel=False)])


        processorReceiver=QuantumProcessor("processorReceiver", num_positions=10,
            mem_noise_models=memNoiseMmodel, phys_instructions=[
            PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_CNOT,duration=10,quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_MEASURE, duration=10,quantum_noise_model=processorNoiseModel, parallel=False)])


        # channels==================================================================
        
        MyCChannel = ClassicalChannel("CChannel_S->R",delay=delay
            ,length=fibre_len)

        nodeSender.connect_to(nodeReceiver, MyCChannel,
                            local_port_name="portC_Sender", remote_port_name="portC_Receiver")

        
        # test example
        # make an EPR pair and origin state
        oriQubit,epr1,epr2=create_qubits(3)
        # epr1,epr2=create_qubits(2)
        # print(measure(oriQubit) , measure(epr1) , measure(epr2))

        # operate(oriQubit, H) # init qubit

        # # set_qstate_formalism(QFormalism.DM)
        # oriQubit , or2=create_qubits(2 , no_state=True)


        oriQubit = AssignStatesBydm([oriQubit] , [np.array([[.4,0.88],[0.88,0.6]])])[0]
        # operate(oriQubit, H) # init qubit
        # operate(oriQubit, H) # init qubit
        print('from main' , MeasureByProb(oriQubit))
        # print(MeasureByProb(epr1))
        # print(MeasureByProb(epr2))
        # print(measure(oriQubit))


        operate(epr1, H)
        operate([epr1, epr2], CNOT)
        # print(measure(oriQubit) , measure(epr1) , measure(epr2))
        # print(measure(oriQubit) , measure(epr1) , measure(epr2))
        # make oriQubit
        #operate(oriQubit, X)
        
        
        myQT_Sender = QuantumTeleportationSender(node=nodeSender,
            processor=processorSender,SendQubit=oriQubit,EPR_1=epr1,portNames=["portC_Sender"])
        myQT_Receiver = QuantumTeleportationReceiver(node=nodeReceiver,
            processor=processorReceiver,EPR_2=epr2,portNames=["portC_Receiver"],bellState=1)
        
        myQT_Receiver.start()
        myQT_Sender.start()
        #ns.logger.setLevel(1)
        stats = ns.sim_run()
        

    return 0


if __name__ == '__main__':
    run_Teleport_sim()