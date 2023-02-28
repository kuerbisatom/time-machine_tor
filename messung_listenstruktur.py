## Messung der Dauer der Deduplikation

import hashlib
from collections import deque
from random import randint
from time import *
list = deque()
ELEMENTS = 50000000
#ELEMENTS = 1000000

for i in range(0,ELEMENTS):
    hash = hashlib.sha256(str(i).encode('utf-8')).hexdigest()
    list.append(hash)
print ("The important Part")
for j in range(0,10):
    ergebnis = 0
    for i in range(0,100):
        check = randint(0,ELEMENTS*10)
        t1 = clock()
        test = hashlib.sha256(str(check).encode('utf-8')).hexdigest()
        if test in (list):
            pass
        else:
            pass
        t2 = clock()
        dt = t2 - t1
        ergebnis += dt
    print ("Ergebnis = " + str(ergebnis/100))
