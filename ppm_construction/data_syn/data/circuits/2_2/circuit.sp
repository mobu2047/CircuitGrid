.title Active DC Circuit
VI0 1 0 0
I 3 1 5
R 0 2 46
F 4 0 VI0 25
I 3 2 5
R 2 5 14
F 6 3 VI0 82
R 5 4 56k
R 6 5 93


.control
op
print i(VI0) ; measurement of I0
print -v(4) ; measurement of U0
print v(5, 6) ; measurement of U4
.endc
.end
