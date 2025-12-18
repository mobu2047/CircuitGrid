.title Active DC Circuit
R 3 0 23
I 0 1 8k
R 2 1 13
I 4 1 26
R 5 2 85
I 0 3 64
R 6 3 1k
I 4 0 16
VI9 0 7 0
R 5 4 45k
R 5 8 77
R 6 7 93m
R 7 4 22k
R 9 7 51
I 8 4 68
R 9 6 40
I 9 4 92k


.control
op
print i(VI9) ; measurement of I9
.endc
.end
