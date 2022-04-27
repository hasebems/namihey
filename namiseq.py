# -*- coding: utf-8 -*-
import time
#import mido
import pygame.midi as pmd
import namiblock as blk

class Seq:
    #   MIDI シーケンスの制御
    #   開始時に生成され、periodic() がコマンド入力とは別スレッドで、定期的に呼ばれる
    #   その他の機能： pygame.midi/mido の生成、CUIに情報を送る
    #   Block: 現状 [0] の一つだけ生成

    def __init__(self, nfl):
        pmd.init()  # MIDI Init

        self.all_ports = []
        self.midi_port = []
        self.scan_midi_all_port()
        self.set_midi_port(0)
        self.start_time = time.time()
        self.during_play = False
        self.blocks = [blk.BlockRegular(self.midi_port), blk.BlockIndependentLoop(self.midi_port)]
        self.current_bk = self.blocks[0]
        self.next_time = 0
        self.current_time = 0
        self.latest_clear_time = 0
        self.fl = nfl

    def scan_midi_all_port(self):
        self.all_ports = []
        devnum = pmd.get_count()
        for i in range(devnum):
            dev = pmd.get_device_info(i)
            if dev[3] == 1: # MIDI Output なら
                name = dev[1].decode()
                self.all_ports.append([i,name,False])
        return self.all_ports

    def set_midi_port(self, idx):
        if idx < len(self.all_ports) and idx >= 0:
            devid = self.all_ports[idx][0]
            self.all_ports[idx][2] = True
        else:
            devid = pmd.get_default_output_id()
            for pt in self.all_ports:
                if devid == pt[0]:
                    pt[2] = True
        try:
            self.midi_port = pmd.Output(devid)
        except:
            devid = -1
        return devid

    def get_tick(self): # for GUI
        tm = self.current_time - self.latest_clear_time
        tick_info = self.current_bk.get_tick_info()
        one_beat = 60/(self.current_bk.tt.bpm*(tick_info[2]/4)) # 1拍の時間
        msr = self.current_bk.tt.crnt_msr + 1

        while tm > one_beat*tick_info[1]:
            tm -= one_beat*tick_info[1]
        # 戻り値： 拍、拍以下の数値0-0.999、小節内の拍数
        return msr, int(tm//one_beat), int((tm%one_beat)*1000/one_beat), tick_info[1]

    def block(self):
        return self.current_bk

    def change_block(self, blk):
        self.current_bk = self.blocks[blk]

    def periodic(self):     # different thread from other functions
        if not self.during_play:
            return
        if self.fl.auto_stop:   # check end of chain loading
            self.current_bk.stop()
            self.during_play = False
            self.fl.auto_stop = False

        self.current_time = time.time() - self.start_time  # calculate elapsed time
        if self.current_time > self.next_time:             # if time of next event come,
            callback = self.fl.read_next_chain_loading if self.fl.chain_loading_state else None
            # Call Block
            self.next_time, clear_ev = self.current_bk.generate_event(self.current_time, callback)
            if self.next_time == blk.STOP_PLAYING:
                self.during_play = False             # Stop playing
            if clear_ev:
                self.latest_clear_time = self.current_time

    def play(self, repeat='on'):
        if self.during_play: return False
        if self.fl.chain_loading_state:
            self.fl.read_first_chain_loading(self.current_bk)   # chain loading
        self.during_play = True
        self.start_time = time.time()                # Get current time
        self.next_time = 0
        self.latest_clear_time = 0
        start_success = self.current_bk.start()
        if self.fl.chain_loading_state:
            self.fl.read_second_chain_loading(self.current_bk)   # chain loading
        return start_success

    def stop(self):
        self.current_bk.stop()
        self.during_play = False

    def fine(self):
        self.current_bk.fine()
