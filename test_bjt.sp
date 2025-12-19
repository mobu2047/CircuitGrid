.title BJT Circuit Test
.MODEL NPN_MODEL NPN (BF=100 IS=1e-14)

R1 VCC N1 10k
R2 N1 0 18k
R3 N2 0 50k
V1 VCC 0 12
Q1 N1 N1 N2 NPN_MODEL

.control
op
print all
.endc
.end
