# -*- coding: utf-8 -*-
#
#   namihey.py   Alpha Version
#
#   from August 15 2020 by M.Hasebe
#
import  threading
import  namiparse as ps
import  namiseq as sq
import  readline    # add history function

def quit():
    global seq
    if seq.duringPlay == True:
        seq.stop()
    pass

def cui():
    while True:
        global pas
        inputText = input(pas.promptStr)
        if inputText == 'quit':
            quit()
            break
        pas.startParsing(inputText)
    global loop
    loop = False

loop = True
seq = sq.Seq()
pas = ps.Parsing(seq)
cuijob = threading.Thread(target=cui)
cuijob.start()
while True:
    seq.periodic()
    if loop == False:
        break
cuijob.join()
print("That's it! Bye!")
