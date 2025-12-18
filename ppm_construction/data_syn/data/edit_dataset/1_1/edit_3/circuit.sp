.title Active DC Circuit
R 1 0 164
R 2 0 38
R 1 3 15
E 2 3 1 3 56k
I 4 2 73
I 5 3 79
R 5 4 56


.control
op
print v(1, 3) ; measurement of U0
.endc
.end
