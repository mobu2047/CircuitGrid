.title Active DC Circuit
I1 1 0 <Empty>
R1 0 3 <Empty>
I2 2 1 <Empty>
R2 1 4 <Empty>
R3 5 2 <Empty>
V1 3 4 <Empty>
R4 5 4 <Empty>


.control
op
print v(1, 2) ; measurement of U5
print v(4, 5) ; measurement of U5
.endc
.end
