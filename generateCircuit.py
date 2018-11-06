from openfermion import *
from openfermionpsi4 import run_psi4
import os
import time
import numpy
import sys

''' To Do:
            Incorporate ability to order Hamiltonian (separate class maybe?)'''
                                                                                
class GenerateCircuit():
    ''' The purpose of this class is to generate a molecule using the 
            openfermionpsi4 package, generate a quantum circuit, save the 
            circuit in QASM output, and provide readouts of various 
            parameters. Progress to be made is the ability to manipulate the
            ordering of the terms in the Hamiltonian for research purposes. '''
            
    def mapping_error(self, mapping):
        ''' A simple helper function to print and exit with an error related
                to an incorrect mapping request. '''
        sys.exit('Error, could not understand mapping: {}. Try "JW" or "BK"'
                 ' in the future.'.format(mapping))
                 
    def check_if_file_already_exists(self, full_filename):
        # Check user input for what to do if renaming the file is required.
        #   Commented out while using slurm services
        
        if(os.path.isfile('./QASMcode/{}'.format(full_filename))):
            
            command = self.file_exists('./QASMcode/{}'.format(full_filename))
            
            if(command == "yes"):
                return full_filename
            elif(command == 'no'):
                sys.exit('User exited program on the grounds that filename'
                          ' is already in use')
            else:
                # Rename file
                full_filename = full_filename[:len(full_filename)-8]
                full_filename += command + '_qasm.txt'
                return full_filename
                
        return full_filename
    
    def file_exists(self, filename):
        ''' This function is used to help determine how to rename a file based
                on client command line input. This function is typically 
                called when the file to save the QASM code already exists.
                Returns either "yes", "no", or an additional descriptor to add 
                to the filename.'''
                
        text = raw_input('''The filename you are trying to save this molecule 
                         under already exists - you may want to check to see if 
                         you have already saved a circuit for this molecule and 
                         mapping. If you would like to override this file, type 
                         "yes". If you would like to cancel, type "no". If you 
                         would like to save this file under an additional 
                         descriptor, type "d [your description here]". Then hit 
                         enter. \n''')
        return self.check_input(text)
        
    def check_input(self, text):
        ''' A recursive helper function to determine the exact command from 
                the client as to how to proceed when rewriting a file. Returns
                either "yes", "no", or an additional descriptor to add to the
                filename.'''
                
        if (text == 'yes'):
            print('overwriting file')
        elif(text == 'no'):
            print('canceling')
        elif(len(text) < 2):
            
            text = raw_input('''Could not recognize your action. Refer to 
                             guidelines written above \n''')
            text = self.check_input(text)
        elif((text[0] == 'd') and (text[1] == ' ')):
            return text[2:]
        else:
            text = raw_input('''Could not recognize your action. Refer to 
                             guidelines written above \n''')
            text = self.check_input(text)
        return text
        
    def get_full_filename(self, mapping):
        ''' A helper function to get the full filename for the saved QASM code
                for a molecule. Requires self.filename to be set first (through
                the "save_qasm()" function. '''
        
        full_filename = None
        
        # Check to make sure that the molecule filename has been set
        if(not self.filename):
            sys.exit('Filename has not been set yet, must execute' 
                     ' "GenerateCircuit.save_qasm()" first.')
        
        # Get file location
        if(mapping == 'JW'):
            full_filename = 'JW_' + self.filename
        elif(mapping == 'BK'):
            full_filename = 'BK_' + self.filename
        else:
            self.mapping_error(mapping)
                     
        return full_filename
        
    def record_gate_counts(self):
        ''' This function is designed to be used to record both the total 
                number of gates and the number of CNOT gates to a file to be
                used for comparison purposes between molecules, mappings, 
                and other various parameters. '''
        
        gate_counts = open('gate_counts.txt', "a")
        
        if((self.jw_gate_count) and (self.jw_CNOT_count)):
            gate_counts.write("{0} {1} {2} {3} {4} {5} {6} {7} {8} {9}"
                              .format(self.name, 'JW', self.molecule.n_qubits,
                              self.basis, self.multiplicity, self.charge,
                              self.active_space_start, self.active_space_stop,
                              self.jw_gate_count, self.jw_CNOT_count))
            gate_counts.write("\n")
        if((self.bk_gate_count) and (self.bk_CNOT_count)):
            gate_counts.write("{0} {1} {2} {3} {4} {5} {6} {7} {8} {9}"
                              .format(self.name, 'BK', self.molecule.n_qubits,
                              self.basis, self.multiplicity, self.charge,
                              self.active_space_start, self.active_space_stop,
                              self.bk_gate_count, self.bk_CNOT_count))
            gate_counts.write("\n")
        gate_counts.close()
        
    def set_gate_count(self, mapping, num_gates, num_CNOT):
        ''' This function is a setter function, designed to be called from the
                "count_gates()" or "count_gates_from_file()" function. It is 
                merely designed to set the variables for the the numbers of
                gates and CNOT gates for the specified mapping. '''
    
        if(mapping == 'JW'):
            self.jw_gate_count = num_gates
            self.jw_CNOT_count = num_CNOT
        elif(mapping == 'BK'):
            self.bk_gate_count = num_gates
            self.bk_CNOT_count = num_CNOT
            
    def count_gates_from_circuit(self, mapping):
        ''' This function takes in the self instance of the class and the type
                of mapping the client would like analyzed. It then counts the 
                total number of gates as well as the number of CNOT gates for 
                the circuit associated with the mapping parameter. In order
                for this function to perform, the circuit variables must be set
                using the "create_circuits()" function.'''
        
        circuit = None
        if(mapping == 'JW'):
            if(self.jw_circuit):
                circuit = self.jw_circuit
            else:
                sys.exit('Circuit not yet generated.')
        elif(mapping == 'BK'):
            if(self.bk_circuit):
                circuit = self.bk_circuit
            else: 
                sys.exit('Circuit not yet generated.')
        elif(mapping == 'both'):
            self.count_gates_from_circuit('JW')
            self.count_gates_from_circuit('BK')
            return 
        else:
            self.mapping_error(mapping)

        if(not circuit):
            sys.exit('Error: Circuit not defined')
            
        num_lines = 0
        num_CNOT = 0
        for line in circuit:
            num_lines += 1
            if(line[0] == 'C'):
                num_CNOT += 1
        
        self.set_gate_count(mapping, num_lines, num_CNOT)
            
    # Not sure if this would be valuable? Maybe post QASM save to save RAM?
    def count_gates_from_file(self, mapping):
        ''' This function takes in the self instance of the class and the type
                of mapping the client would like analyzed. It then opens the
                saved QASM output file for the circuit and counts the total
                number of gates as well as the number of CNOT gates. In order
                for this function to perform, the circuit must be saved first
                using the "save_qasm()" function.'''
                
        full_filename = self.get_full_filename(mapping) 
        
        # Count lines (aka gates)
        file = open("./QASMcode/{}".format(full_filename), "r")
        
        num_lines = 0
        num_CNOT = 0
        for line in file:
            num_lines += 1
            if(line[0] == 'C'): #Indicates a CNOT gate
                num_CNOT += 1
        
        file.close()
        
        self.set_gate_count(mapping, num_lines, num_CNOT)
        
        # print('The total number of gates required for the {} mapping of {} is '
        #       '{}'.format(mapping, self.name, num_lines))
        # print('The number of CNOT gates required is {}'.format(num_CNOT))
    
    def save_qasm(self, mapping):
        ''' This function is designed to save the circuit generated by the 
                OpenFermion package in QASM format into a file in the 
                QASMcode subdirectory. The filename is in the format:
                [mapping]_[molecule name]_[basis]_[multiplicity]_[charge]_
                [active space start]_to_[active_space_stop]_[description]_
                qasm.txt. In order for this function to perform, a molecule must
                be generated through the "load_molecule()" and 
                "create_hamiltonians()" functions.'''
        
        # Set filename for the QASM output. Mapping prefix set after.
        self.filename = "{}_{}_{}_{}_{}_to_{}_{}_qasm.txt".format(self.name, 
                    self.basis, self.multiplicity, self.charge, 
                    self.active_space_start, self.active_space_stop, 
                    self.description)
        
        full_filename = self.get_full_filename(mapping)
        
        # Determination of which mapping is being used
        circuit = None
        if(mapping == 'JW'):
            circuit = self.jw_circuit
        elif(mapping == 'BK'):
            circuit = self.bk_circuit
        else:
            self.mapping_error(mapping)
            
        if(not circuit):
            sys.exit("Error: Circuit not yet defined")
            
        # full_filename = self.check_if_file_already_exists(full_filename)
        
        file = open("./QASMcode/{}".format(full_filename), "w")
       
        for line in circuit:
            file.write(line)
            file.write("\n")
    
        file.close()
        
    #NOT USED TIL MAG_ORDERING READY
    def absolute_value(coefficient):
        ''' This is a simply function to use the numpy.absolute() function
                to determine the magnitude of complex numbers.'''
        return numpy.absolute(coefficient[1])
        
    #NOT READY
    def magnitude_ordering(hamiltonian):
        ''' This function is designed to take a Hamiltonian and rearrange the
                terms to fit a magnitude ordering. Magnitude ordering arranges
                the terms by ordering them based on the descending magnitude
                of the coefficient. This may possibly be moved out of this class
                in the future.'''
    
        sorted_terms = sorted(hamiltonian.terms.iteritems(), key=absolute_value)
        print(sorted_terms[0])
        mag_ordered_operator = QubitOperator(sorted_terms[0][0], sorted_terms[0][1])
        # print(mag_ordered_operator)
            
        i = 1
        for term in sorted_terms:
            if (i != 1):
                print(term)
                mag_ordered_operator += QubitOperator(term[0], term[1])
                # print(mag_ordered_operator)
                print('')
            i += 1
        print(mag_ordered_operator.terms)
        # return 0
        # return sorted(hamiltonian.iteritems(), key=absolute_value)
        
    def create_hamiltonians(self):
        ''' This function is designed to generate the fermion hamiltonian and
                qubit hamiltonians for both the Jordan-Wigner and 
                Bravyi-Kitaev mappings. This function should be called after
                the "load_molecule()" function is called to ensure proper 
                usage.'''
        
        # If not client defined, generates based on maximum orbitals
        if(not self.active_space_start):
            self.active_space_start = 0
        if(not self.active_space_stop):
            if(self.molecule):
                self.active_space_stop = (self.molecule.n_qubits/2)
        
        # Get the Hamiltonian in an active space.
        molecular_hamiltonian = self.molecule.get_molecular_hamiltonian(
            occupied_indices=range(self.active_space_start),
            active_indices=range(self.active_space_start, 
                                 self.active_space_stop))
        
        self.fermion_hamiltonian = get_fermion_operator(molecular_hamiltonian)
        
    def create_circuits(self, mapping):
        ''' A simple function to generate the circuits for both the 
                Jordan-Wigner and Bravyi-Kitaev mappings. For this function
                to work properly, the "create_hamiltonians()" function must
                be called first.'''
                
        if(mapping == 'JW'):
            self.qubit_hamiltonian_jw = jordan_wigner(self.fermion_hamiltonian)
            self.jw_circuit = pauli_exp_to_qasm([self.qubit_hamiltonian_jw])
        elif(mapping == 'BK'):
            self.qubit_hamiltonian_bk = bravyi_kitaev(self.fermion_hamiltonian)
            self.bk_circuit = pauli_exp_to_qasm([self.qubit_hamiltonian_bk])
        elif(mapping == 'both'):
            self.qubit_hamiltonian_jw = jordan_wigner(self.fermion_hamiltonian)
            self.qubit_hamiltonian_bk = bravyi_kitaev(self.fermion_hamiltonian)
            self.jw_circuit = pauli_exp_to_qasm([self.qubit_hamiltonian_jw])
            self.bk_circuit = pauli_exp_to_qasm([self.qubit_hamiltonian_bk])
        else:
            self.mapping_error(mapping)
            
    def load_molecule(self):
        ''' This function is designed to initialize the molecule through
                the use of the OpenFermion and OpenFermion-Psi4 packages. In 
                order for this function to perform properly, a molecule's
                parameters must be set through the use of the setter 
                functions. The parameters required are: name, geometry, basis, 
                multiplicity, and charge.'''
        
        # Generate and populate instance of MolecularData.
        if(self.description != ''):
            molecule = MolecularData(self.geometry, self.basis, 
                                     self.multiplicity, self.charge,
                                     self.description)
        else:
            molecule = MolecularData(self.geometry, self.basis, 
                                     self.multiplicity, self.charge)
        
        # Determine if integrals have been previously generated or not
        if not(os.path.exists(molecule.filename + '.hdf5')):
        
            # Set calculation parameters.
            run_scf, run_mp2, run_cisd, run_ccsd, run_fci = 1, 1, 1, 1, 1

            molecule = run_psi4(molecule, run_scf=run_scf, run_mp2=run_mp2,
                                run_cisd=run_cisd, run_ccsd=run_ccsd,
                                run_fci=run_fci)
            
            # Save molecule for future, so that regeneration is not required
            molecule.save()
            molecule.load()
        else:
            molecule.load()
        
        self.molecule = molecule
        self.name = self.name.replace(" ", "_")
        
    def print_qubits(self):
        ''' A simple helper output function to easily print how many qubits are
                required for full simulation of the molecule and how many
                are required for simulation of the molecule based on the 
                specified active spaces.'''
                
        print('''Number of Qubits needed for full molecule simulation of {}
                is {} and the number needed for simulation based on active 
                orbitals is {}'''.format(self.name, self.molecule.n_qubits, 
                count_qubits(self.fermion_hamiltonian))) 
       
    def set_name(self, name):
        ''' Setter function '''
        self.name = name
        
    def set_geometry(self, geometry):
        ''' Setter function '''
        self.geometry = geometry
    
    def get_geometry_from_pubchem(self):
        ''' Setter function; Must be used after self.name is defined '''
        self.geometry = geometry_from_pubchem(self.name)
        
    def set_basis(self, basis):
        ''' Setter function '''
        self.basis = basis
        
    def set_multiplicity(self, multiplicity):
        ''' Setter function '''
        self.multiplicity = multiplicity
    
    def set_charge(self, charge):
        ''' Setter function '''
        self.charge = charge
        
    def set_active_space_start(self, start):
        ''' Setter function '''
        self.active_space_start = start
        
    def set_active_space_stop(self, stop):
        ''' Setter function '''
        self.active_space_stop = stop
    
    def set_description(self, description):
        ''' Setter function '''
        self.description = description
    
    def __init__(self):
        ''' Initialize empty instances '''
        self.name = None
        self.geometery = None
        self.basis = None
        self.multiplicity = None
        self.charge = None
        self.active_space_start = None
        self.active_space_stop = None
        self.description = ''
        self.filename = None
        self.qubit_hamiltonian_jw = None
        self.qubit_hamiltonian_bk = None
        self.molecule = None
        self.fermion_hamiltonian = None
        self.jw_circuit = None
        self.bk_circuit = None
        self.jw_gate_count = None
        self.jw_CNOT_count = None
        self.bk_gate_count = None
        self.bk_CNOT_count = None

 
def timeit(function, parameter):
    ''' A function used for testing speed performance of a function. Input is
            of the form: variable = timeit(function, parameter)'''
            
    start = time.time()
    
    result = function(parameter)
    
    end = time.time()
    runtime = end-start
    
    print('The runtime of {} is {}'.format(function, runtime))
    return result

      
