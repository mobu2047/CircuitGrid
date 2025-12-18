.title Active DC Circuit
R2 1 N10 <Empty>
VI5 0 N10 0
G1 0 1 0 1 <Empty>
I1 0 1 <Empty>
VI2 1 2 0
R3 1 N12 <Empty>
VI8 2 N12 0
I2 2 3 <Empty>
V1 1 3 <Empty>
R1 4 1 <Empty>
R4 4 3 <Empty>


.control
op
print i(VI5) ; measurement of I5
print -v(1) ; measurement of U5
print i(VI2) ; measurement of I2
print i(VI8) ; measurement of I8
.endc
.end
