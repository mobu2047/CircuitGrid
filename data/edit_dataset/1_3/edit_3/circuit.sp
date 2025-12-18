.title Active DC Circuit
R 0 1 65
V 4 0 69
R 1 5 81m
I 2 1 49k
V 1 6 78m
R 3 2 23
R 7 2 59
R 3 8 92
V 9 4 20
R 6 5 54
R 10 5 92
R 6 7 94
R 11 6 44k
V 7 8 37
VI0 7 12 0
I 8 13 95
E 9 10 8 13 85
I 10 11 3
R 11 12 73k
V 13 12 42


.control
op
print v(2, 3) ; measurement of U8
print i(VI0) ; measurement of I0
print v(8, 13) ; measurement of U3
.endc
.end
