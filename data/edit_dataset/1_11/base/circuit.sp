.title Active DC Circuit
I 1 0 61
F 0 3 VI4 67
I 2 1 28m
R 4 N41 35k
VI4 1 N41 0
R 5 N52 93
VI9 2 N52 0
I 4 3 92k
VI8 3 6 0
R 5 4 57
R 4 5 37m
I 6 5 45


.control
op
print i(VI4) ; measurement of I4
print i(VI9) ; measurement of I9
print v(3, 4) ; measurement of U4
print i(VI8) ; measurement of I8
.endc
.end
