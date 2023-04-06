from netsquid.protocols import NodeProtocol
from netsquid.components import QSource,Clock,QuantumProgram
from netsquid.components.qsource import SourceStatus
from netsquid.components.instructions import INSTR_H,INSTR_CNOT,INSTR_MEASURE,INSTR_MEASURE_X
from netsquid.qubits import measure , reduced_dm

import sys
scriptpath = "../../lib/"
sys.path.append(scriptpath)
from functions import Compare_basis,Random_basis_gen




class QG_A_qPrepare(QuantumProgram):
    
    def __init__(self,num_bits=1):
        self.num_bits=num_bits
        super().__init__()
        
    def program(self):
        qList_idx=self.get_qubit_indices(2*self.num_bits)
        # create multiEPR
        for i in range(2*self.num_bits):
            if i%2==0:                           # List A case
                self.apply(INSTR_H, qList_idx[i])
            else:                                # List B case
                self.apply(INSTR_CNOT, [qList_idx[i-1], qList_idx[i]])
        yield self.run(parallel=False)


class QG_A_measure(QuantumProgram):
    def __init__(self,basisList,num_bits):
        self.basisList=basisList
        self.num_bits=num_bits
        super().__init__()


    def program(self):   
        for i in range(0,len(self.basisList*2),2):
            if self.basisList[int(i/2)] == 0:           # only even slot       
                self.apply(INSTR_MEASURE, 
                    qubit_indices=i, output_key=str(i),physical=True)  # standard basis
            else:                              # 1 case 
                self.apply(INSTR_MEASURE_X, 
                    qubit_indices=i, output_key=str(i),physical=True) # Hadamard basis
        yield self.run(parallel=False)
 



class AliceProtocol(NodeProtocol):
    
    def __init__(self,node,processor,num_bits,sourceFreq,
                port_names=["portQA_1","portCA_1","portCA_2"]):
        super().__init__()
        self.num_bits=num_bits
        self.node=node
        self.processor=processor
        self.portNameQ1=port_names[0]
        self.portNameC1=port_names[1]
        self.portNameC2=port_names[2]
        self.EPRList=None
        self.basisList=Random_basis_gen(self.num_bits)
        # self.basisList=[1] * self.num_bits
        self.loc_measRes=[]
        self.loc_measRes2=[]
        self.key=None
        self.sourceQList=[]
        self.sourceFreq=sourceFreq
        
        #generat qubits from source
        self.A_Source = QSource("Alice_source"
            ,status=SourceStatus.EXTERNAL) # enable frequency
        self.A_Source.ports["qout0"].bind_output_handler(self.storeSourceOutput)
        
    # =======================================A run ============================
    def run(self):

        
        # A generat qubits
        self.A_genQubits(self.num_bits,self.sourceFreq)
        
        # wait
        yield self.await_program(processor=self.processor)
        
        
        #yield self.await_program(processor=self.processor)
        # send qubits
        self.A_sendEPR()
        
        print('basis for A ' , self.basisList)

        #self.A_measure()
        self.myQG_A_measure=QG_A_measure(
            basisList=self.basisList,num_bits=self.num_bits)
        self.processor.execute_program(
            self.myQG_A_measure,qubit_mapping=[i for  i in range(0, 2*self.num_bits)])
        
        yield self.await_program(processor=self.processor)


        # receive B basis
        port=self.node.ports[self.portNameC1]
        yield self.await_port_input(port)
        basis_B = port.rx_input().items
        
        
        


        # get A meas
        #self.processor.set_program_done_callback(self.A_getPGoutput,once=True)
        for i in range(2*self.num_bits):
            if i%2 == 0:  # only even slot
                tmp=self.myQG_A_measure.output[str(i)][0]
                self.loc_measRes.append(tmp)
        print('measurement by A 1: ' , self.loc_measRes)
        
        # send A basis to B
        self.node.ports[self.portNameC2].tx_output(self.basisList)


        # -----------------===================------------
        # self.myQG_A2_measure=QG_A_measure(
        # basisList=self.basisList,num_bits=self.num_bits)
        # self.processor.execute_program(
        #     self.myQG_A2_measure,qubit_mapping=[i for  i in range(0, 2*self.num_bits)])
        
        # yield self.await_program(processor=self.processor)
        # for i in range(2*self.num_bits):
        #     if i%2 == 0:  # only even slot
        #         tmp=self.myQG_A2_measure.output[str(i)][0]
        #         self.loc_measRes2.append(tmp)
        # print('measurement by A 2: ' , self.loc_measRes2)
        # self.loc_measRes2=Compare_basis(self.basisList,basis_B,self.loc_measRes2)
        # print('##Key A: ' , ''.join(map(str, self.loc_measRes2)))
        # --------------====================-----------
        inx=list(range(0,2*self.num_bits,2))
        payload=self.processor.pop(inx)
        for i in range(self.num_bits):
            print(measure(payload[i]))

        print('-------basis in B ------')
        print('A: ' , self.basisList)
        print('B: ' , basis_B)
        print('------------------')

        # compare basis
        self.loc_measRes=Compare_basis(self.basisList,basis_B,self.loc_measRes)


        
        self.key=''.join(map(str, self.loc_measRes))
        #print("A key:",self.key)

    def storeSourceOutput(self,qubit):
        self.sourceQList.append(qubit.items[0])
        if len(self.sourceQList)==2*self.num_bits:
            self.processor.put(qubits=self.sourceQList)
            
            # apply H detector
            PG_qPrepare=QG_A_qPrepare(num_bits=self.num_bits)
            self.processor.execute_program(
                PG_qPrepare,qubit_mapping=[i for  i in range(0, 2*self.num_bits)])


    def A_genQubits(self,num,freq=8e7):
        
        
        #set clock
        clock = Clock("clock", frequency=freq, max_ticks=2*num)
        try:
            clock.ports["cout"].connect(self.A_Source.ports["trigger"])
        except:
            pass
            #print("alread connected") 
            
        clock.start()
        
            
    def A_sendEPR(self):
        #print("A_sendEPR")
        inx=list(range(1,2*self.num_bits+1,2))
        payload=self.processor.pop(inx)
        self.node.ports[self.portNameQ1].tx_output(payload)


        
