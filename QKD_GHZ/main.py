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

import time

from random import randint

from Alice import QuantumTeleportationSender,key_len
from Bob import QuantumTeleportationReceiver

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import AssignStatesBydm , MeasureByProb,get_fidelity,it_reset,get_bit_error


def run_Teleport_sim(runtimes=10,fibre_len=10**-9,memNoiseMmodel=None,processorNoiseModel=None,delay=0
               ,loss_init=0,loss_len=0,QChV=3*10**-4,CChV=3*10**-4):
    
    for i in range(runtimes): 
        link_len = 100
        delay = 0
        mem_depolar_rate = 10000
        depolar_rate = 0
        
        ns.sim_reset()
        print('====running:' , i , '===========')

        mem_noise_model = None
        # nodes====================================================================

        nodeSender   = Node("SenderNode"    , port_names=["portC_Sender" , "portC_Sender2" , 'portQ_Sender' , 'portQ_Sender2'])
        nodeReceiver = Node("ReceiverNode"  , port_names=["portC_Receiver" , 'portQ_Receiver'])
        nodeReceiver2 = Node("ReceiverNode2"  , port_names=["portC_Receiver2" , 'portQ_Receiver2'])

        # processors===============================================================
        processorSender=QuantumProcessor("processorSender", num_positions=1000,
            mem_noise_models=mem_noise_model, phys_instructions=[
            PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_CNOT,duration=1,quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_MEASURE, duration=1,quantum_noise_model=processorNoiseModel, parallel=False),
            PhysicalInstruction(INSTR_MEASURE_BELL, duration=2,quantum_noise_model=processorNoiseModel, parallel=False)])


        processorReceiver=QuantumProcessor("processorReceiver", num_positions=1,
            mem_noise_models=mem_noise_model, phys_instructions=[
            PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_CNOT,duration=1,quantum_noise_model=processorNoiseModel),
            PhysicalInstruction(INSTR_MEASURE, duration=1,quantum_noise_model=processorNoiseModel, parallel=False)])
        # processorReceiver2=QuantumProcessor("processorReceiver2", num_positions=100,
        #     mem_noise_models=memNoiseMmodel, phys_instructions=[
        #     PhysicalInstruction(INSTR_X, duration=1, quantum_noise_model=processorNoiseModel),
        #     PhysicalInstruction(INSTR_Z, duration=1, quantum_noise_model=processorNoiseModel),
        #     PhysicalInstruction(INSTR_H, duration=1, quantum_noise_model=processorNoiseModel),
        #     PhysicalInstruction(INSTR_CNOT,duration=10,quantum_noise_model=processorNoiseModel),
        #     PhysicalInstruction(INSTR_MEASURE, duration=10,quantum_noise_model=processorNoiseModel, parallel=False)])


        # channels==================================================================

        q_delay = 1
        q_depolar_rate = 1e10
        q_dephase_rate = 1e8
        MyQChannel=QuantumChannel("QChannel_A->B",delay=q_delay
            ,length=link_len
            ,models={
             "quantum_loss_model": FibreLossModel(p_loss_init=0.1, p_loss_length=0, rng=None)
            ,"delay_model": None
            ,"quantum_noise_model":DepolarNoiseModel(depolar_rate=q_depolar_rate, time_independent=False)
            })

        # MyQChannel2=QuantumChannel("QChannel_A->C",delay=delay
        #     ,length=5000
        #     ,models={"myFibreLossModel": FibreLossModel(p_loss_init=.1, p_loss_length=.1, rng=None)
        #     ,"mydelay_model": FibreDelayModel(c=2.083*10**5)
        #     ,"myFibreNoiseModel":DepolarNoiseModel(depolar_rate=0.1, time_independent=False)})
        
        
        nodeSender.connect_to(nodeReceiver, MyQChannel,
            local_port_name =nodeSender.ports["portQ_Sender"].name,
            remote_port_name=nodeReceiver.ports["portQ_Receiver"].name)

        # nodeSender.connect_to(nodeReceiver2, MyQChannel2,
        #     local_port_name =nodeSender.ports["portQ_Sender2"].name,
        #     remote_port_name=nodeReceiver2.ports["portQ_Receiver2"].name)
        
        MyCChannel = ClassicalChannel("CChannel_S->R",delay=delay
            ,length=link_len
            ,models={"myFibreLossModel": FibreLossModel(p_loss_init=.1, p_loss_length=.1, rng=None)
            ,"mydelay_model": FibreDelayModel(c=2.083*10**5)
            # ,"mydelay_model": None
            ,"myFibreNoiseModel":DepolarNoiseModel(depolar_rate=depolar_rate, time_independent=False)})

        # MyCChannel2 = ClassicalChannel("CChannel_S->R2",delay=delay
        #     ,length=fibre_len)

        nodeSender.connect_to(nodeReceiver, MyCChannel,
                            local_port_name="portC_Sender", remote_port_name="portC_Receiver")
        

        # nodeSender.connect_to(nodeReceiver2, MyCChannel2,
        #                     local_port_name="portC_Sender2", remote_port_name="portC_Receiver2")

        
        myQT_Sender = QuantumTeleportationSender(node=nodeSender,
            processor=processorSender,portNames=["portC_Sender" , "portC_Sender2"])
        myQT_Receiver = QuantumTeleportationReceiver(node=nodeReceiver,
            processor=processorReceiver,portNames=["portC_Receiver" , "portQ_Receiver"],bellState=1)

        # myQT_Receiver2 = QuantumTeleportationReceiver(node=nodeReceiver2,
        #     processor=processorReceiver2,portNames=["portC_Receiver2", "portQ_Receiver2"],bellState=1)
        
        myQT_Receiver.start()
        # myQT_Receiver2.start()
        myQT_Sender.start()
        stats = ns.sim_run()


    return 0


if __name__ == '__main__':
    start = time.time()


    run_Teleport_sim()
    end = time.time()
    print('total time ', end - start)