# -*- coding: utf-8 -*-
#
#   namihey.py   Alpha Version
#
#   from August 15 2020 by M.Hasebe
#
import  threading
import  namiparse as ps
import  namiseq as sq
import  namiseq2 as sq2
import  namilib as nlib
import  namigui as ngui
import  namifile as nfl
import  namimidi as midi
import  readline    # add history function

def quit_job(seq):
    if seq.during_play:
        seq.stop()
    pass

def cui(loop, seq, pas):
    while True:
        input_text = input(pas.prompt_str)
        if input_text == 'quit' or input_text == 'exit':
            quit_job(seq)
            break
        pas.startParsing(input_text)
    loop.running = False

def generate_ev(loop, seq, seq2, pas):
    while True:
        seq.periodic()
        seq2.periodic()
        seq.file_auto_play(pas)
        if not loop.running:
            break

def main():
    # Start from here!
    loop = ngui.Loop()
    fl = nfl.NamiFile()
    md = midi.Midi()
    seq = sq.Seq(fl,md)
    seq2 = sq2.Seq2()
    pas = ps.Parsing(seq,seq2,fl,md)
    gui = ngui.NamiGui()
    pas.midi_setting(pas.CONFIRM_MIDI_OUT_ID)

    cui_job = threading.Thread(target=cui, args=(loop, seq, pas))
    cui_job.start()
    ev_job = threading.Thread(target=generate_ev, args=(loop, seq, seq2, pas))
    ev_job.start()
    gui.main_loop(loop,seq,seq2,pas,fl)

    cui_job.join()
    ev_job.join()

    nlib.log.save_file()
    pas.print_dialogue("That's it! Bye!")

if __name__ == '__main__':
    main()
