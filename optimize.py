from llist import dllist

GATETYPES = ["H", "CNOT", "Rx", "Rz"];

class gate():
	def __init__(self):
		self.gateType = 4;
		self.coefficient = 0;
		self.controlQubit = -1;
		self.targetQubit = -1;

	def canCancel(self, other):
		if((self.gateType == other.gateType) and 
		   (self.controlQubit == other.controlQubit) and
		   (self.targetQubit == other.targetQubit)):
			return 1;
		if((self.gateType == other.gateType) and
			((self.controlQubit == other.targetQubit) or
			 (self.targetQubit == other.controlQubit))):
			return 1
		return 0;

	def canCommute(self, other):
		if((self.gateType == 2) and (other.gateType == 2)):
			return 1;
		elif((self.gateType == 3) and (other.gateType == 3)):
			return 1;
		elif((self.gateType == 0) and (other.gateType == 0)):
			return 1;
		elif((self.gateType != 1) and (other.gateType != 1)):
			if(self.controlQubit != other.controlQubit):
				return 1;
			else:
				return 0;
		elif((self.gateType == 1) and (other.gateType == 3)):
			if(self.targetQubit != other.controlQubit):
				return 1;
			else:
				return 0;
		elif((self.gateType == 3) and (other.gateType == 1)):
			if(self.controlQubit != other.targetQubit):
				return 1;
			else:
				return 0;
		else:
			return(not self.checkQubits(self.controlQubit, self.targetQubit,
					other.controlQubit, other.targetQubit));

	def checkQubits(self, c1, t1, c2, t2):
		if(c1 == c2):
			return 1;
		elif(c1 == t2):
			return 1;
		elif(c2 == t1):
			return 1;
		elif(t1 == -1):
			return 0;
		elif(t2 == -1):
			return 0;
		elif(t1 == t2):
			return 1;
		else:
			return 0;

class circuit():
	def __init__(self):
		self.length = 0;
		self.numCNOT = 0;
		self.optimizedLength = 0;
		self.optimizedNumCNOT = 0;
		self.Gates = dllist();

	def add(self, gate):
		self.Gates.append(gate);
		self.length += 1;
		self.optimizedLength += 1;
		if(gate.gateType == 1):
			self.numCNOT += 1;
			self.optimizedNumCNOT += 1;

	def addAndOptimize(self, gate):
		# print("Adding ")
		# print(GATETYPES[gate.gateType])
		# print("To circuit:")
		# self.printgates();
		self.length += 1;
		self.optimizedLength += 1;
		if(gate.gateType == 1):
			self.numCNOT += 1;
			self.optimizedNumCNOT += 1;
		if(not self.cancelNext(gate)):
			self.Gates.append(gate);
		# print("Resulting in")
		# self.printgates();

	def cancelNext(self, gate):
		cancelled = 0;
		nextGate = self.Gates.last;

		while(nextGate):
			if(gate.canCancel(nextGate.value)):
				self.removeNext(gate, nextGate);
				cancelled = 1;
				break;
			elif(gate.canCommute(nextGate.value)):
				nextGate = nextGate.prev;
			else:
				break;

		return cancelled;

	def removeNext(self, gate, nextGate):
		# print("Removing")
		# print(GATETYPES[nextGate.value.gateType]);
		if((nextGate.value.gateType == 2) or (nextGate.value.gateType == 3)):
			nextGate.value.coefficient += gate.coefficient;
			self.optimizedLength -= 1;

			if(nextGate.value.coefficient >= 62831853071795864):
				nextGate.value.coefficient -= 62831853071795864;

			if(nextGate.value.coefficient <= -62831853071795864):
				nextGate.value.coefficient += 62831853071795864;

			if(nextGate.value.coefficient == 0):
				self.optimizedLength -= 1;
				self.removeGate(nextGate);
		else:
			if(gate.gateType == 1):
				self.optimizedNumCNOT -= 2;
			self.optimizedLength -= 2;
			self.removeGate(nextGate);

	def optimize(self):
		oldLength = self.optimizedLength;
		self.cancelDuplicates();
		newLength = self.optimizedLength;

		while(newLength != oldLength):
			oldLength = newLength;
			self.cancelDuplicates();
			newLength = self.optimizedLength;

	def cancelDuplicates(self):
		currentGate = self.Gates.first;

		while(currentGate):
			nextGate = currentGate.next;
			ifCancelledGate = currentGate.prev;
			cancelled = 0;

			while(nextGate):
				if(currentGate.value.canCancel(nextGate.value)):
					self.cancelGates(currentGate, nextGate);
					cancelled = 1;
					break;
				elif(currentGate.value.canCommute(nextGate.value)):
					nextGate = nextGate.next;
				else:
					break;

			if(cancelled):
				currentGate = ifCancelledGate;
			else:
				currentGate = currentGate.next;

	def cancelGates(self, currentGate, nextGate):
		if((currentGate.value.gateType == 2) or (currentGate.value.gateType == 3)):
			currentGate.value.coefficient += nextGate.value.coefficient;
			self.removeGate(nextGate);
			# print("Removing")
			# print(GATETYPES[nextGate.value.gateType]);
			# print("Combining with")
			# print(GATETYPES[currentGate.value.gateType]);
			self.optimizedLength -= 1;

			if(currentGate.value.coefficient == 0):
				# print("Removing")
				# print(GATETYPES[currentGate.value.gateType]);
				self.removeGate(currentGate);
				self.optimizedLength -= 1;
		else:
			# print("Removing")
			# print(GATETYPES[nextGate.value.gateType]);
			# print("with")
			# print(GATETYPES[currentGate.value.gateType]);
			if(currentGate.value.gateType == 1):
				self.optimizedNumCNOT -= 2;
			self.optimizedLength -= 2;
			self.removeGate(nextGate);
			self.removeGate(currentGate);
		# print;

	def printgates(self):
		for gate in self.Gates:
			text = GATETYPES[gate.gateType] + ' ' + str(gate.coefficient);
			text = text + ' ' + str(gate.controlQubit) + ' ';
			text = text + str(gate.targetQubit);
			print(text);

	def removeGate(self, gate):
		self.Gates.remove(gate);


# g = gate();
# g.gateType = 0;
# g.coefficient = 1.123;
# g.controlQubit = 3;
# g.targetQubit = 2;

# a = gate();
# a.gateType = 1;
# a.coefficient = 232.32;
# a.controlQubit = 6;
# a.targetQubit = 5;

# c = circuit();
# c.addAndOptimize(g);
# c.printgates();
# print(c.length);
# print(c.numCNOT);
# print(c.optimizedLength);
# print(c.optimizedNumCNOT);
# print;
# c.addAndOptimize(a);
# c.printgates();
# print(c.length);
# print(c.numCNOT);
# print(c.optimizedLength);
# print(c.optimizedNumCNOT);
# print;
# c.addAndOptimize(a);
# c.printgates();
# print(c.length);
# print(c.numCNOT);
# print(c.optimizedLength);
# print(c.optimizedNumCNOT);

# print;
# print;
# print;

# d = circuit();
# d.add(g);
# d.printgates();
# print(d.length);
# print(d.numCNOT);
# print(d.optimizedLength);
# print(d.optimizedNumCNOT);
# print;
# d.add(a);
# d.printgates();
# print(d.length);
# print(d.numCNOT);
# print(d.optimizedLength);
# print(d.optimizedNumCNOT);
# print;
# d.add(a);
# d.printgates();
# print(d.length);
# print(d.numCNOT);
# print(d.optimizedLength);
# print(d.optimizedNumCNOT);
# print;
# d.optimize();
# d.printgates();
# print(d.length);
# print(d.numCNOT);
# print(d.optimizedLength);
# print(d.optimizedNumCNOT);





