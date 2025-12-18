.title Active DC Circuit
R 1 0 91
VI0 0 3 0
I 2 1 95
VI4 1 4 0
R 5 2 13k
R 3 1 2
R 3 6 83
V 4 1 19k
V 1 7 26
I 5 4 40
R 6 7 37
R 8 7 15k
R 8 5 44


.control
op
print i(VI0) ; measurement of I0
print v(1, 2) ; measurement of U4
print i(VI4) ; measurement of I4
print v(3, 6) ; measurement of U2
.endc
.end
