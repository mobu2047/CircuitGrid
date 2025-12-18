.title Active DC Circuit
R 0 2 26k
R 1 0 2m
V 2 0 24
I 1 3 43k
R 2 4 2
G 3 2 8 10 15
R 3 6 57
I 5 4 69
R 4 7 4m
R 5 6 83
R 5 8 90
R 6 8 43k
VI9 7 8 0
R 7 9 40
R 8 10 43
I 10 8 43
I 9 10 56k


.control
op
print i(VI9) ; measurement of I9
print v(8, 10) ; measurement of U0
.endc
.end
