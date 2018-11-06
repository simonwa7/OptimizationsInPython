from generateCircuit import GenerateCircuit
from optimize import circuit, gate
import sys
import time
import array

def getCircuit(name, geometry, basis, multiplicity, charge, mapping):
    # Load appropraite molecule
    molecule = GenerateCircuit() 
    molecule.set_name(name)
    if(geometry == "pubchem"):
        molecule.get_geometry_from_pubchem()
    else:
        molecule.set_geometry(geometry)
    molecule.set_basis('sto-3g')
    molecule.set_multiplicity(multiplicity)
    molecule.set_charge(charge)
    molecule.load_molecule() 
    molecule.create_hamiltonians()
    molecule.create_circuits(mapping)
    if(mapping == "BK"):
        return molecule.bk_circuit
    elif(mapping == "JW"):
        return molecule.jw_circuit
    else:
        sys.exit("Didn't understand mapping")
        
def getMoleculeData(name, geometry, basis, multiplicity, charge):
    # Load appropraite molecule
    molecule2 = GenerateCircuit() 
    molecule2.set_name(name)
    if(geometry == "pubchem"):
        molecule2.get_geometry_from_pubchem()
    else:
        molecule2.set_geometry(geometry)
    molecule2.set_basis('sto-3g')
    molecule2.set_multiplicity(multiplicity)
    molecule2.set_charge(charge)
    molecule2.load_molecule() 
    molecule2.create_hamiltonians()
    data = array.array('i', [0, 0, 0]) 
    data[0] = molecule2.molecule.n_qubits
    data[1] = molecule2.active_space_start
    data[2] = molecule2.active_space_stop
    return data

def lineToGate(line):
    g = gate();
    gateTypeString = "";

    i = 0;
    while(line[i] != ' '):
        gateTypeString += line[i];
        i += 1;
    i += 1;

    if(gateTypeString == "H"): 
        g.gateType = 0; 
        g.controlQubit = int(line[i:]); 
    elif(gateTypeString == "CNOT"): 
        g.gateType = 1; 
        controlQubitstr = "";
        while((line[i] != " ")):
            controlQubitstr += line[i];
            i += 1;
        g.controlQubit = int(controlQubitstr); 
        i += 1;
        g.targetQubit = int(line[i:]); 
    else: 
        if(gateTypeString == "Rx"):
            g.gateType = 2; 
        elif(gateTypeString == "Rz"):
            g.gateType = 3; 
        else: 
            print("Trouble identifying gate type"); 

        coeff_index = getCoefficient(line, i); 
        g.coefficient = coeff_index[0]; 
        i = int(coeff_index[1]); 
        g.controlQubit = int(line[i:]); 
    return g;

def getCoefficient(line, i):
    untypedCoefficient = "";
    result = [0, 0];
    
    while(line[i] != ' '):
        untypedCoefficient += line[i];
        i += 1;
    
    result[1] = i;

    digit = 0;
    while(untypedCoefficient[digit] != '.'):
        if(untypedCoefficient[digit] == ' '):
            break;
        
        digit += 1;
    
    while(len(untypedCoefficient) < 18):
        untypedCoefficient += '0';
    
    coeff = untypedCoefficient[:digit] + untypedCoefficient[digit+1:];
    result[0] = long(coeff);

    return result;
    
    
def main():
    # Parse input arguements
    name = str(sys.argv[1])
    basis = "sto-3g"
    if(len(sys.argv) == 6):
        geometry = str(sys.argv[2])
        multiplicity = int(sys.argv[3])
        charge = int(sys.argv[4])
        mapping = str(sys.argv[5])
    elif((len(sys.argv)-5)%4 == 0):
        multiplicity = int(sys.argv[2])
        charge = int(sys.argv[3])
        mapping = str(sys.argv[4])
        geometry = list()
        num_atoms = (len(sys.argv)-5)/4
        for index in range(num_atoms):
            atom_index = (index*4)+5
            atom = tuple((str(sys.argv[atom_index]), (float(sys.argv[atom_index+1]),float(sys.argv[atom_index+2]),float(sys.argv[atom_index+3]))))
            geometry.append(atom)
        
    print(geometry)
    name = name.replace("_", " ")
    
    start = time.time()
    circuitOF = getCircuit(name, geometry, basis, multiplicity, charge, mapping)
    time_to_generate = time.time()-start
    
    name = name.replace(" ", "_")
    
    if(mapping == "BK"):
        print("BRAVYI-KITAEV MAPPING\n")
    elif(mapping == "JW"):
        print("\nJORDAN-WIGNER MAPPING")

    C = circuit();
    gatesfromOF = 0;
        
    start = time.time()
    for line in circuitOF:
        gatesfromOF += 1;
        g = gate();
        g = lineToGate(line);
        C.addAndOptimize(g)
    time_to_loop = time.time()-start
        
    print("Gate numbers prior to optimization:")   
    print("Total Gates: ")
    gate_count = C.length;
    print(gate_count)
    print("CNOT Gates: ")
    CNOT_count = C.numCNOT;
    print(CNOT_count)
        
    start = time.time()
    C.optimize()
    time_to_optimize = time.time()-start
        
    print("\nGate numbers after optimization:")  
    print("Total Gates: ")
    optimized_gate_count = C.optimizedLength;
    print(optimized_gate_count)
    print("CNOT Gates: ")
    optimized_CNOT_count = C.optimizedNumCNOT;
    print(optimized_CNOT_count)
    
    # qcircuit.clear("circuit")
    
    print("\nTIMINGS")
    
    if(mapping == "BK"):
        print("BRAVYI-KITAEV")
        print("Time for OpenFermion Generation of BK Mapping: {}".format(time_to_generate))
        print("Time for Looping of BK Mapping: {}".format(time_to_loop))
        print("Time for Optimization of BK Mapping: {}".format(time_to_optimize))
    elif(mapping == "JW"):
        print("JORDAN-WIGNER")
        print("Time for OpenFermion Generation of JW Mapping: {}".format(time_to_generate))
        print("Time for Looping of JW Mapping: {}".format(time_to_loop))
        print("Time for Optimization of JW Mapping: {}".format(time_to_optimize))
        
        
    name = name.replace("_", " ")
    data = getMoleculeData(name, geometry, basis, multiplicity, charge)
    name = name.replace(" ", "_")

    recorded_data = open('datav3.txt', "a") 
    recorded_data.write("{0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12} {13} {14} {15}\n"
                     .format(name, mapping, data[0], 
                             basis, multiplicity, charge, 
                             data[1], 
                             data[2],
                             gate_count, CNOT_count, 
                             optimized_gate_count, optimized_CNOT_count,
                             time_to_generate, time_to_loop,
                             time_to_optimize,
                             gatesfromOF)
                     )
                     
    recorded_data.close();
    
main()