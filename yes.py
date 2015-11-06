import sys

import time

message = "yes"
cpt = 0

if len(sys.argv) == 2:
    message = sys.argv[1]

while 1:
    print cpt, message
    cpt += 1
    time.sleep(1)
