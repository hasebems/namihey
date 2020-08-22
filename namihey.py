# -*- coding: utf-8 -*-
#
#   namihey.py   Alpha Version
#
#   from August 15 2020 by M.Hasebe
#
import  threading
import  namiparse as ps
import  namiseq as sq

def quit():
    global seq
    if seq.duringPlay == True:
        seq.stop()
    pass

def cui():
    while True:
        inputText = input("~~~> ")
        if inputText == 'quit':
            quit()
            break
        global seq
        ps.parse(inputText,seq)
    global loop
    loop = False

loop = True
seq = sq.Seq()
cuijob = threading.Thread(target=cui)
cuijob.start()
while True:
    seq.playSeq()
    if loop == False:
        break
cuijob.join()
print("That's it! Bye!")
