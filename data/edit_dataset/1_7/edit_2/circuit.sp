.title Active DC Circuit
E 0 1 5 6 7
G 0 4 5 6 52k
R 1 2 60
R 4 1 44m
I 3 2 22
R 6 3 96k
R 7 4 59
V 4 N45 43
VI9 N45 5 0
V 4 8 32
R 5 6 35k
V 6 9 9
R 7 8 83
R 8 5 12
V 5 9 69k


.control
op
print i(VI9) ; measurement of I9
print v(5, 6) ; measurement of U5
.endc
.end
