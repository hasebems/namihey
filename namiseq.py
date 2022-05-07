# -*- coding: utf-8 -*-
import time
import namiblock as blk
import namilib as nlib

class Seq:
    #   開始時に生成され、periodic() がコマンド入力とは別スレッドで、定期的に呼ばれる。
    #   そのため、change_tempo, play, stop 受信時はフラグのみを立て、periodic()
    #   で実処理を行う。
    def __init__(self, nfl, md):
        self.during_play = False
        self.block = blk.Block(md)
        self.start_time = 0
        self.current_time = 0
        self.current_tick = 0   # quarter note = 480
        self.next_tick = 0
        self.tempo = 120
        self.one_tick_time = 1/((self.tempo/60)*480)
        self.tempo_for_periodic = 0 # 0 means False, others True
        self.play_for_periodic = False
        self.stop_for_periodic = False
        self.fine_for_periodic = False
        self.fl = nfl

    def file_auto_play(self, pas):
        if self.fl.auto_stop:   # check end of chain loading
            self.block.stop()
            self.during_play = False
            self.fl.auto_stop = False
            pas.print_dialogue("The End!")

    def get_tick(self): # for GUI
        bi = self.block.get_beat_info()
        tick_for_onemsr = bi[0]
        tick_for_beat = nlib.DEFAULT_TICK_FOR_ONE_MEASURE/bi[2]
        tick_inmsr = self.current_tick-self.block.abs_tick_of_msrtop
        count = tick_for_onemsr//tick_for_beat
        beat = tick_inmsr//tick_for_beat
        tick = tick_inmsr%tick_for_beat
        return self.block.abs_msr_counter,int(beat),int(tick),int(count)

    def start(self):
        if self.fl.chain_loading_state:
            self.fl.read_first_chain_loading(self.block)   # chain loading
        self.start_time = time.time()                # Get current time
        self.current_time = 0
        self.current_tick = 0   # quarter note = 480
        self.next_tick = 0
        self.next_time = 0
        self.block.start()
        if self.fl.chain_loading_state:
            self.fl.read_second_chain_loading(self.block)   # chain loading

    def periodic(self):     # different thread from other functions
        if self.play_for_periodic and not self.during_play:
            self.play_for_periodic = False
            self.start()
            self.during_play = True

        if self.stop_for_periodic:
            self.stop_for_periodic = False
            self.block.stop()
            self.during_play = False

        if self.fine_for_periodic:
            self.fine_for_periodic = False
            self.block.fine()

        if self.tempo_for_periodic != 0:
            self.tempo = self.tempo_for_periodic
            self.tempo_for_periodic = 0
            self.one_tick_time = 1/((self.tempo/60)*480)

        if not self.during_play:
            return
        total_time = time.time() - self.start_time
        diff_time = total_time - self.current_time
        while diff_time > self.one_tick_time:
            self.current_tick += 1
            diff_time -= self.one_tick_time
            self.current_time = total_time
        if self.current_tick > self.next_tick:  # if time of next event come,
            callback = self.fl.read_next_chain_loading if self.fl.chain_loading_state else None
            # Call Block
            self.next_tick = self.block.generate_event(self.current_tick, callback)
            if self.next_tick == blk.STOP_PLAYING:
                self.during_play = False             # Stop playing

    def blk(self):
        return self.block

    def change_tempo(self, tempo):
        self.tempo_for_periodic = tempo

    def play(self):
        self.play_for_periodic = True
        if self.during_play is False:
            return True
        else:
            return False

    def stop(self):
        self.stop_for_periodic = True

    def fine(self):
        self.fine_for_periodic = True
        