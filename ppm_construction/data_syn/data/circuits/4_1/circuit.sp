.title Active DC Circuit
R 1 0 16
V 4 0 89k
V 1 2 89
I 1 5 43k
R 2 3 75m
R 3 7 30k
R 5 4 66
VI0 5 6 0
I 8 5 50
R 7 6 75
R 6 9 89
R 10 7 38k
R 4 8 18
R 11 4 43k
R 8 9 89
F 8 12 VI7 23
R 9 N910 37
VI4 N910 10 0
F 13 9 VI7 64
R 10 14 35
R 12 11 13k
R 15 11 12
R 12 16 86
R 13 14 71k
VI7 17 13 0
R 18 14 26k
V 15 16 59
E 17 16 5 4 88
E 19 16 10 7 63
R 18 17 74k
R 17 20 82
I 21 18 65k
R 19 15 84
R 20 19 60
R 21 20 6


.control
op
print v(4, 5) ; measurement of U1
print i(VI0) ; measurement of I0
print v(7, 10) ; measurement of U0
print v(8, 12) ; measurement of U7
print i(VI4) ; measurement of I4
print i(VI7) ; measurement of I7
.endc
.end
