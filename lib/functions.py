import netsquid as ns
from netsquid.components.instructions import *
from netsquid.components.qprogram import *
from netsquid.components.qprocessor import *
from netsquid.qubits.qubitapi import assign_qstate, reduced_dm




it_reset = 0


'''
Assign certain quantum states to bubits.
input:
    qList: The qubit list to operate on.
    dmList: The density matrix to assign.
output:
    qList: qubit list which are assgined with given states.
'''
def AssignStatesBydm(qList,dmList):
    if len(qList)!=len(dmList):
        print("Error! List length does not match!")
        return 1
    for i,j in enumerate(qList):
        #print("F qList[0]:",qList[i],"dmList[0]:",dmList[i])
        assign_qstate(qList[i], dmList[i], formalism=ns.qubits.QFormalism.DM) #ns.qubits.QFormalism.DM

    return qList

def MeasureByProb(qubit , do_print = False):

    dm = reduced_dm(qubit)
    # print(dm)
    # alpha = complex(dm[0][0]).real()
    alpha = complex(str(dm[0][0]).replace(')' , '').replace('(' , ''))
    beta = complex(str(dm[1][1]).replace(')' , '').replace('(' , ''))
    if do_print:
        print(alpha.real , beta.real)
    if alpha.real > beta.real:
        return 0
    return 1
def MeasureProb(qubit):
    dm = reduced_dm(qubit)
    alpha = complex(str(dm[0][0]).replace(')' , '').replace('(' , ''))
    beta = complex(str(dm[1][1]).replace(')' , '').replace('(' , ''))

    return alpha.real , beta.real


def add_it_count(count , i):
    global it_reset
    it_reset += count
    # print('it_reset ' , it_reset , count , i)
    return 0
def get_fidelity(qbit):
    fid = ns.qubits.fidelity(
            qbit, ns.qubits.outerprod((ns.S*ns.H*ns.s0).arr), squared=True)
    return fid

def get_bit_error(sent_key , received_key):
    error = 0
    for i in range(0,len(sent_key)):
        if sent_key[i] != received_key[i]:
            error += 1
    return error










def ProgramFail(info):
    print(info)
    print("programe failed!!")    
    

    