.title Active DC Circuit
R3 1 0 <Empty>
R4 2 1 <Empty>
I1 1 4 <Empty>
I2 2 3 <Empty>
R1 5 3 <Empty>
R5 4 0 <Empty>
R6 4 2 <Empty>
R7 5 2 <Empty>
R2 2 5 <Empty>
R8 4 0 <Empty>
R9 4 5 <Empty>


.control
op
print v(1, 2) ; measurement of U3
print v(1, 4) ; measurement of U1
print v(2, 5) ; measurement of U8
.endc
.end
