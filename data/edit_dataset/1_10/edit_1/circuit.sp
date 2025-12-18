.title Active DC Circuit
R 1 N10 86
VI0 0 N10 0
V 0 3 8
R 2 1 87
R 4 2 57k
R 3 1 33
E 5 3 6 5 28
R 6 1 2
R 4 2 19
R 4 7 12k
V 8 2 42
R 6 5 80
V 6 7 41
I 8 7 87m


.control
op
print i(VI0) ; measurement of I0
print v(3, 1) ; measurement of U6
print v(5, 6) ; measurement of U1
.endc
.end
