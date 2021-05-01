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
import  namigui as ngui
import  readline    # add history function

def midi_setting(seq, pas):
    midi_port = seq.get_midi_all_port()
    pas.print_dialogue("==MIDI OUT LIST==")
    for i, pt in enumerate(midi_port):
        pas.print_dialogue("PORT " + str(i) + ": " + str(pt))
    pas.print_dialogue("==SELECTED MIDI OUT==")
    pas.print_dialogue(seq.get_midi_port())

def quit_job(seq):
    if seq.during_play:
        seq.stop()
    pass

def cui(loop, seq, pas):
    while True:
        input_text = input(pas.promptStr)
        if input_text == 'quit' or input_text == 'exit':
            quit_job(seq)
            break
        pas.startParsing(input_text)
    loop.running = False

def generate_ev(loop, seq):
    while True:
        seq.periodic()
        if not loop.running:
            break

def main():
    # Start from here!
    loop = ngui.Loop()
    seq = sq.Seq()
    pas = ps.Parsing(seq)
    gui = ngui.NamiGui()
    midi_setting(seq, pas)

    cui_job = threading.Thread(target=cui, args=(loop, seq, pas))
    cui_job.start()
    ev_job = threading.Thread(target=generate_ev, args=(loop, seq))
    ev_job.start()
    gui.main_loop(loop, seq)

    cui_job.join()
    ev_job.join()

    nlib.log.save_file()
    pas.print_dialogue("That's it! Bye!")

if __name__ == '__main__':
    main()
