.title Active DC Circuit
R 0 3 73
E 1 0 1 2 82k
V 0 3 71
R 1 2 69k
V 1 4 51m
R 2 5 82
R 4 3 86k
R 5 4 57


.control
op
print v(1, 2) ; measurement of U0
.endc
.end
