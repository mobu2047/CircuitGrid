.title Active DC Circuit
R 2 0 67m
V 1 0 44
VI0 0 3 0
R 1 4 27
E 3 2 2 5 13
R 2 5 72
R 4 3 38
R 3 6 41
V 7 4 13k
R 5 6 30
R 7 N76 66
VI5 6 N76 0


.control
op
print i(VI0) ; measurement of I0
print v(2, 5) ; measurement of U0
print i(VI5) ; measurement of I5
.endc
.end
