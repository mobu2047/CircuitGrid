.title Active DC Circuit
G 0 1 4 3 82k
R 0 2 75
R 3 1 61m
R 1 N15 48
VI8 N15 5 0
R 2 3 4k
I 4 3 85
V 5 4 10


.control
op
print i(VI8) ; measurement of I8
print v(2, 3) ; measurement of U4
print v(3, 4) ; measurement of U2
.endc
.end
