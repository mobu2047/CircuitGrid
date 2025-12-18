.title Active DC Circuit
R 0 2 15
R 3 0 11
G 0 1 3 4 56k
V 0 N04 57
VI6 N04 4 0
R 1 4 15
R 3 2 9m
R 3 4 34


.control
op
print i(VI6) ; measurement of I6
print v(3, 4) ; measurement of U0
.endc
.end
