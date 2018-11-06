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
    molecule.save_qasm(mapping)
        

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
    getCircuit(name, geometry, basis, multiplicity, charge, mapping)
    time_to_generate = time.time()-start

main();