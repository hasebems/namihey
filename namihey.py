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
    if seq.during_play == True:
        seq.stop()
    pass

def cui():
    while True:
        global pas
        inputText = input(pas.promptStr)
        if inputText == 'quit' or inputText == 'exit':
            quit()
            break
        pas.startParsing(inputText)
    global loop
    loop = False

loop = True
seq = sq.Seq()
pas = ps.Parsing(seq)
pas.print_dialogue("MIDI OUT: " + seq.get_midi_port())
cuijob = threading.Thread(target=cui)
cuijob.start()
while True:
    seq.periodic()
    if loop == False:
        break
cuijob.join()
pas.print_dialogue("That's it! Bye!")
