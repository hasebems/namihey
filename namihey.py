# -*- coding: utf-8 -*-
#
#   namihey.py   Alpha Version
#
#   from August 15 2020 by M.Hasebe
#
import  threading
import  namiparse as ps
import  namiseq as sq
import  namilib as nlib
import  readline    # add history function

def quit_job():
    global seq
    if seq.during_play:
        seq.stop()
    pass

def cui():
    while True:
        global pas
        input_text = input(pas.promptStr)
        if input_text == 'quit' or input_text == 'exit':
            quit_job()
            break
        pas.startParsing(input_text)
    global loop
    loop = False

def midi_setting():
    global pas
    global seq
    midi_port = seq.get_midi_all_port()
    pas.print_dialogue("==MIDI OUT LIST==")
    for i, pt in enumerate(midi_port):
        pas.print_dialogue("PORT " + str(i) + ": " + str(pt))
    pas.print_dialogue("==SELECTED MIDI OUT==")
    pas.print_dialogue(seq.get_midi_port())

# Start from here!
loop = True
seq = sq.Seq()
pas = ps.Parsing(seq)
midi_setting()

cui_job = threading.Thread(target=cui)
cui_job.start()
while True:
    seq.periodic()
    if not loop:
        break
cui_job.join()
nlib.log.save_file()
pas.print_dialogue("That's it! Bye!")
