# -*- coding: utf-8 -*-
import namilib as nlib

####
#   SeqPlay Obj. の Interface
class SeqPlay:

    def __init__(self, obj, md, type):
        self.parent = obj
        self.md = md
        self.type = type

    # Seqplay thread内でコール
    def start(self):    # User による start/play 時にコールされる
        pass

    def stop(self):     # User による stop 時にコールされる
        pass

    def fine(self):     # User による fine があった次の小節先頭でコールされる
        pass

    def msrtop(self,msr):           # 小節先頭でコールされる
        pass

    def periodic(self,msr,tick):    # 再生中、繰り返しコールされる
        pass

    def destroy_me(self):   # 自クラスが役割を終えた時に True を返す
        return False

####
#   起動時から存在し、決して destroy されない SeqPlay Obj.
class SeqPart(SeqPlay):

    def __init__(self, obj, md, num):
        super().__init__(obj, md, 'Part')
        self.part_num = num
        self.measure_count = 0
        self.loop_obj = None
        self.state_play = False
        self.keynote = nlib.DEFAULT_NOTE_NUMBER
        self.description = [None for _ in range(4)]

        self.loop_measure = 3

    def _generate_loop(self):
        if self.part_num != 0: return # とりあえず part1 のみ
        self.loop_obj = Loop(self.parent, self.md)
        self.parent.add_sqobj(self.loop_obj)

    def _generate_sequence(self):
        pass

    ## Seqplay thread内でコール
    def start(self):
        self.state_play = True

    def msrtop(self,msr):
        self.measure_count = msr
        if self.measure_count%self.loop_measure == 0:
            self._generate_loop()

    #def periodic(self,msr,tick):
    #    pass

    def destroy_me(self):
        return False    # 最後まで削除されない

    def stop(self):
        self.state_play = False

    def fine(self):
        self.stop()

    ## CUI thread内でコール
    def change_keynote(self, nt):
        self.keynote = nt
        if self.state_play:
            self.state_reserve = True
        else:
            self._generate_sequence()

    def change_cc(self, cc_num, val):
        if val >= 0 and val < 128:
            self.volume = val
            self.md.send_control(self.midich, cc_num, val)

    def clear_description(self):
        self.add_seq_description(['phrase',None,None,None])

    def add_seq_description(self, data):
        self.description = data
        if self.state_play:
            self.state_reserve = True
        else:
            self._generate_sequence()

####
#   １行分の Phrase/Pattern を生成するための SeqPlay Obj.
#   １周期が終わったら、destroy され、また新しいオブジェクトが Part によって作られる
#   Loop 内のデータに基づき、Note Obj. を生成する
class Loop(SeqPlay):

    # example
    LOOP_LENGTH = 3

    def __init__(self, obj, md):
        super().__init__(obj, md, 'Loop')
        self.first_measure_num = -1
        self.measure_count = 0
        self.whole_tick = self.parent.get_tick_for_onemsr() * self.LOOP_LENGTH # example
        self.destroy = False

        # example
        self.count = 0

    def _set_note(self,ev):
        obj = Note(self.parent, self.md, ev)
        self.parent.add_sqobj(obj)

    def msrtop(self,msr):
        # 初回コール時
        if self.first_measure_num == -1:
            self.first_measure_num = msr

    def periodic(self,msr,tick):
        elapsed_tick = (msr - self.first_measure_num)*self.parent.get_tick_for_onemsr() + tick
        if elapsed_tick >= self.whole_tick:
            self.destroy = True
            return

        # example for generating Note Event
        cnt = self.count
        lpmsr = msr - self.first_measure_num
        if lpmsr == (cnt//4) and tick > (cnt%4)*480:
            note = cnt%12
            self.count += 1
            self._set_note([0,0x3c+note,0x7f,100])

    def destroy_me(self):
        return self.destroy

    def stop(self):
        self.destroy = True


####
#   一音符の SeqPlay Obj.
#   Note On時に生成され、MIDI を出力した後、Note Offを生成して destroy される
class Note(SeqPlay):

    def __init__(self, obj, md, ev):
        super().__init__(obj, md, 'Note')
        self.midi_ch = ev[0]
        self.note_num = ev[1]
        self.velocity = ev[2]
        self.duration = ev[3]
        self.during_noteon = False
        self.destroy = False
        self.off_msr = 0
        self.off_tick = 0

    def _note_on(self):
        if self.note_num > 127 or self.velocity > 127: return
        self.md.send_midi_note(self.midi_ch, self.note_num, self.velocity)

    def _note_off(self):
        self.destroy = True
        self.during_noteon = False
        # midi note off
        if self.note_num > 127 or self.velocity > 127: return
        self.md.send_midi_note(self.midi_ch, self.note_num, 0)

    def periodic(self,msr,tick):
        if not self.during_noteon:
            self.during_noteon = True
            tk = self.parent.get_tick_for_onemsr()
            self.off_msr = msr
            self.off_tick = tick + self.duration
            while self.off_tick > tk:
                self.off_tick -= tk
                self.off_msr += 1
            # midi note on
            self._note_on()
        else:
            if msr == self.off_msr and tick > self.off_tick:
                self._note_off()

    def destroy_me(self):
        return self.destroy

    def stop(self):
        if self.during_noteon:
            self._note_off()
