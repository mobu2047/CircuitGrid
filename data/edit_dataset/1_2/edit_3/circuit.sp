.title Active DC Circuit
R 1 0 22
R 0 2 71
I 3 1 6
I 2 3 26
R 2 4 2
R 3 5 11
E 4 5 3 1 7k


.control
op
print v(1, 3) ; measurement of U3
.endc
.end
