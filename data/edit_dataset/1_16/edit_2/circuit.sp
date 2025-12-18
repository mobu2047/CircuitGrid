.title Active DC Circuit
V 0 1 32
V 0 2 53m
R 1 3 18k
R 2 N23 26
VI6 N23 3 0
R 3 2 50
R 2 4 910k
R 3 4 96k


.control
op
print v(1, 3) ; measurement of U4
print i(VI6) ; measurement of I6
print v(2, 3) ; measurement of U7
.endc
.end
