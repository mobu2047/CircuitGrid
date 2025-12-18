.title Active DC Circuit
G 1 0 1 0 40
E 2 N20 1 0 35m
VI2 0 N20 0
R 4 1 42
V 2 3 6
R 4 3 74m


.control
op
print -v(1) ; measurement of U9
print i(VI2) ; measurement of I2
.endc
.end
