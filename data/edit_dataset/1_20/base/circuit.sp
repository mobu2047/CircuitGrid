.title Active DC Circuit
E 1 0 3 0 53k
R 3 0 82
R 2 1 92m
R 4 N41 20m
VI9 1 N41 0
V 4 3 63
R 2 4 17k
V 5 4 56
V 4 6 51k
R 2 7 63
I 5 6 5m
R 7 6 67k


.control
op
print -v(3) ; measurement of U4
print i(VI9) ; measurement of I9
.endc
.end
