.title Active DC Circuit
R 0 1 44
VI8 2 1 0
R 1 4 96k
R 3 2 80
R 2 3 6
V 4 0 77k
I 5 0 53m
V 4 6 54
R 7 3 2
R 3 7 3
R 6 5 37k
V 7 6 20k


.control
op
print i(VI8) ; measurement of I8
.endc
.end
