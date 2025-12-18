.title Active DC Circuit
R 0 1 28k
R 0 3 90
R 2 1 38m
V 1 N14 78
VI4 N14 4 0
I 5 2 56
V 4 3 73
V 6 N63 37
VI0 3 N63 0
V 6 4 1
R 5 7 16
V 6 7 81m


.control
op
print i(VI4) ; measurement of I4
print i(VI0) ; measurement of I0
.endc
.end
