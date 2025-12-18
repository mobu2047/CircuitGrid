.title Active DC Circuit
G 0 1 4 7 27
V 0 3 9k
E 2 1 4 7 93
R 1 4 89m
R 2 4 62k
R 3 4 26k
E 5 3 4 7 11
I 4 7 81k
R 5 6 95m
I 5 7 96
R 7 6 54
V 7 N76 6
VI9 6 N76 0


.control
op
print v(4, 7) ; measurement of U
print v(5, 6) ; measurement of U0
print v(6, 7) ; measurement of U2
print i(VI9) ; measurement of I9
.endc
.end
