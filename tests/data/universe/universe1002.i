Sample for universe test
c cell section
c main universe cells
3 0   #(-1 -3) #(-2  3 -4)       IMP:N=0 IMP:P=0
4 21 -0.9   -1 -3 6 -7 -8     IMP:N=1 IMP:P=1
5 22 -7.8   -1 -3 6 -7 8 -9  IMP:N=1 IMP:P=1
6 23 -1.8   -1 -3 5 -6 -9     IMP:N=1 IMP:P=1
7 0         -1 -3 #(6 -7 -8) #(6 -7 8 -9) #(5 -6 -9) IMP:N=1 IMP:P=1
8 10 -2.7   -2  3 -4 -10 11  12  IMP:N=1 IMP:P=1
9 11 0.1003 -2  3 -4 -11 12 -13  IMP:N=1 IMP:P=1
10 0        -2  3 -4  #(-10 11  12) #(-11 12 -13)   IMP:N=1 IMP:P=1

c surface section
c surfaces of main universe
1 SX -2 3
2 CX 2
3 PX 0
4 PX 6
5 PX -6
6 PX -3
7 PX -1
8 CX  2
9 CX  4
10 SX 6 1
11 PX 4
12 PX 1
13 CX 1

c data section
m10 6012.21c 1
m11 1001.21c -0.11191 8016.50c -0.88809
m21 1001.21c 2 6012.21c 1
m22 26056.21c 1
m23 5010.21c -1
