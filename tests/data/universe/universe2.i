Sample for universe test
c cell section
c main universe cells
1 0   -1 -3     FILL=2  IMP:N=1 IMP:P=1
2 0   -2  3 -4  FILL=1 (-2 0 0) IMP:N=1 IMP:P=1
3 0   #1 #2     IMP:N=0 IMP:P=0
c universe 1 cells
10 10 -2.7   -10 11  12 U=1 IMP:N=1 IMP:P=1
11 11 0.1003 -11 12 -13 U=1 IMP:N=1 IMP:P=1
12 0          #10 #11   U=1 IMP:N=1 IMP:P=1
c universe 2 cells
21 21 -0.9   21 -22 -23    U=2 IMP:N=1 IMP:P=1
22 22 -7.8   21 -22 23 -24 U=2 IMP:N=1 IMP:P=1
23 23 -1.8   20 -21 -24    U=2 IMP:N=1 IMP:P=1
24 0         #21 #22 #23   U=2 IMP:N=1 IMP:P=1

c surface section
c surfaces of main universe
1 SX -2 3
2 CX 2
3 PX 0
4 PX 6
c universe 1 surfaces
10 1 SX 6 1
11 1 PX 4
12 1 PX 1
13 1 CX 1
c universe 2 surfaces
20 PX -6
21 PX -3
22 PX -1
23 CX  2
24 CX  4

c data section
tr1 2 0 0
m10 6012.21c 1
m11 1001.21c -0.11191 8016.50c -0.88809
m21 1001.21c 2 6012.21c 1
m22 26056.21c 1
m23 5010.21c -1
