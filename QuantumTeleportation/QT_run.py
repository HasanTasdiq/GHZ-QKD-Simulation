import numpy as np
import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.protocols import NodeProtocol
from netsquid.qubits.operators import X,H,CNOT , Z
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
from netsquid.components.models.qerrormodels import FibreLossModel,T1T2NoiseModel,DepolarNoiseModel,DephaseNoiseModel


from random import randint

from QT_sender import QuantumTeleportationSender,key_len
from QT_receiver import QuantumTeleportationReceiver

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import AssignStatesBydm , MeasureByProb,get_fidelity

def run_Teleport_sim(runtimes=1,fibre_len=10**-9,memNoiseMmodel=None,processorNoiseModel=None,delay=0
               ,loss_init=0,loss_len=0,QChV=3*10**-4,CChV=3*10**-4):
    
    
    
    for i in range(runtimes): 
        
        ns.sim_reset()

        # nodes====================================================================

        nodeSender   = Node("SenderNode"    , port_names=["portC_Sender" , "portC_Sender2" , 'portQ_Sender' , 'portQ_Sender2'])
        nodeReceiver = Node("ReceiverNode"  , port_names=["portC_Receiver" , 'portQ_Receiver'])
        nodeReceiver2 = Node("ReceiverNode2"  , port_names=["portC_Receiver2" , 'portQ_Receiver2'])

        # processors===============================================================
        processorSender=QuantumProcessor("processorSender", num_positions=200,
            mem_noise_models=memNoiseMmodel, phys_instructions=[
            PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_CNOT,duration=10,quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_MEASURE, duration=10,quantum_noise_model=processorNoiseModel, parallel=False),
            PhysicalInstruction(INSTR_MEASURE_BELL, duration=10,quantum_noise_model=processorNoiseModel, parallel=False)])


        processorReceiver=QuantumProcessor("processorReceiver", num_positions=100,
            mem_noise_models=memNoiseMmodel, phys_instructions=[
            PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_CNOT,duration=10,quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_MEASURE, duration=10,quantum_noise_model=processorNoiseModel, parallel=False)])
        processorReceiver2=QuantumProcessor("processorReceiver2", num_positions=100,
            mem_noise_models=memNoiseMmodel, phys_instructions=[
            PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_CNOT,duration=10,quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_MEASURE, duration=10,quantum_noise_model=processorNoiseModel, parallel=False)])


        # channels==================================================================

        MyQChannel=QuantumChannel("QChannel_A->B",delay=0
            ,length=5000
            ,models={"myFibreLossModel": FibreLossModel(p_loss_init=.1, p_loss_length=.1, rng=None)
            ,"mydelay_model": FibreDelayModel(c=2.083*10**5)
            ,"myFibreNoiseModel":DepolarNoiseModel(depolar_rate=0.1, time_independent=False)})

        MyQChannel2=QuantumChannel("QChannel_A->C",delay=0
            ,length=5000
            ,models={"myFibreLossModel": FibreLossModel(p_loss_init=.1, p_loss_length=.1, rng=None)
            ,"mydelay_model": FibreDelayModel(c=2.083*10**5)
            ,"myFibreNoiseModel":DepolarNoiseModel(depolar_rate=0.1, time_independent=False)})
        
        
        nodeSender.connect_to(nodeReceiver, MyQChannel,
            local_port_name =nodeSender.ports["portQ_Sender"].name,
            remote_port_name=nodeReceiver.ports["portQ_Receiver"].name)

        nodeSender.connect_to(nodeReceiver2, MyQChannel2,
            local_port_name =nodeSender.ports["portQ_Sender2"].name,
            remote_port_name=nodeReceiver2.ports["portQ_Receiver2"].name)
        
        MyCChannel = ClassicalChannel("CChannel_S->R",delay=delay
            ,length=fibre_len)

        MyCChannel2 = ClassicalChannel("CChannel_S->R2",delay=delay
            ,length=fibre_len)

        nodeSender.connect_to(nodeReceiver, MyCChannel,
                            local_port_name="portC_Sender", remote_port_name="portC_Receiver")
        

        nodeSender.connect_to(nodeReceiver2, MyCChannel2,
                            local_port_name="portC_Sender2", remote_port_name="portC_Receiver2")

        
        n_qubits = key_len
        # test example
        # make an EPR pair and origin state
        qubits=create_qubits(n_qubits + 1)
        # epr1,epr2=create_qubits(2)
        # print(measure(oriQubit) , measure(epr1) , measure(epr2))

        # operate(oriQubit, H) # init qubit

        # # set_qstate_formalism(QFormalism.DM)
        # oriQubit , or2=create_qubits(2 , no_state=True)


        # oriQubit = AssignStatesBydm([oriQubit] , [np.array([[.4,0.88],[0.88,0.6]])])[0]
        # operate(oriQubit, H) # init qubit
        # operate(oriQubit, H) # init qubit
        # print('from main' , MeasureByProb(oriQubit))
        # print(MeasureByProb(epr1))
        # print(MeasureByProb(epr2))
        # print(measure(oriQubit))


        # operate(epr0, H)
        # operate([epr0, epr1], CNOT)
        # operate([epr1, epr2], CNOT)


    
        # print(measure(oriQubit) , measure(epr1) , measure(epr2))
        # print(measure(oriQubit) , measure(epr1) , measure(epr2))
        # make oriQubit
        #operate(oriQubit, X)

        # print(MeasureByProb(qubits[0]))

        operate(qubits[0] , H)

        # for i in range(0 , n_qubits ):
        #     operate([qubits[i] , qubits[i+1]] , CNOT)

        for i in range(1 , n_qubits + 1 ):
            operate([qubits[0] , qubits[i]] , CNOT)


        # tq1 = qubits.pop()
        # tq2 = qubits.pop()
        # operate([tq1 , tq2] , CNOT)
        # operate(tq1 , H)
        # print(measure(tq1))
        # print(measure(tq2))
        
        receivers_qbit = qubits.pop()


        # tq1 , tq2=create_qubits(2)

        # operate(tq1 , H)
        # operate([tq1 , tq2] , CNOT)

        # operate([receivers_qbit , tq1] , CNOT)
        # operate(receivers_qbit , H)

        # z = measure(receivers_qbit)[0]
        # x = measure(tq1)[0]

        # if z == 1:
        #     operate(tq2 , Z)
        # if x == 1:
        #     operate(tq2 , X)

        # print('zzz ' , z)

        # operate([qubits[0] , receivers_qbit], CNOT)
        # operate(qubits[0] , H)
        # print(measure(qubits[0]) )

        # print('fidelity of bob qbit' , get_fidelity(receivers_qbit) )
        
        
        myQT_Sender = QuantumTeleportationSender(node=nodeSender,
            processor=processorSender,portNames=["portC_Sender" , "portC_Sender2"])
        myQT_Receiver = QuantumTeleportationReceiver(node=nodeReceiver,
            processor=processorReceiver,portNames=["portC_Receiver" , "portQ_Receiver"],bellState=1)

        myQT_Receiver2 = QuantumTeleportationReceiver(node=nodeReceiver2,
            processor=processorReceiver2,portNames=["portC_Receiver2", "portQ_Receiver2"],bellState=1)
        
        myQT_Receiver.start()
        # myQT_Receiver2.start()
        myQT_Sender.start()
        #ns.logger.setLevel(1)
        stats = ns.sim_run()
        

    return 0


if __name__ == '__main__':
    run_Teleport_sim()