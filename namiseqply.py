# -*- coding: utf-8 -*-
import namilib as nlib

####
#   SeqPlay Obj. の Interface
class SeqPlay:

    def __init__(self, obj, md, type):
        self.parent = obj
        self.md = md
        self.type = type

    # 以下の IF は Seqplay thread内でコール
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
class Part(SeqPlay):

    def __init__(self, obj, md, num):
        super().__init__(obj, md, 'Part')
        self.part_num = num
        self.measure_count = 0
        self.loop_measure = 3       # sample
        self.loop_obj = None

    def _generate_loop(self):
        if self.part_num != 0: return # とりあえず part1 のみ
        self.loop_obj = Loop(self.parent, self.md, self.loop_measure)
        self.parent.add_sqobj(self.loop_obj)

    def start(self):
        pass

    def msrtop(self,msr):
        self.measure_count = msr
        if self.measure_count%self.loop_measure == 0:
            self._generate_loop()

    def periodic(self,msr,tick):
        pass

    def destroy_me(self):
        return False    # 最後まで削除されない


####
#   １行分の Phrase/Pattern を生成するための SeqPlay Obj.
#   １周期が終わったら、destroy され、また新しいオブジェクトが Part によって作られる
#   Loop 内のデータに基づき、Note Obj. を生成する
class Loop(SeqPlay):

    def __init__(self, obj, md, msr):
        super().__init__(obj, md, 'Loop')
        self.max_measure_num = msr
        self.first_measure_num = -1
        self.measure_count = 0
        self.count = 0
        self.destroy = False

    def _set_note(self,ev):
        obj = Note(self.parent, self.md, ev)
        self.parent.add_sqobj(obj)

    def msrtop(self,msr):
        # 初回コール時
        if self.first_measure_num == -1:
            self.first_measure_num = msr

        self.measure_count = msr - self.first_measure_num
        if self.measure_count >= self.max_measure_num:
            self.destroy = True

    def periodic(self,msr,tick):
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
        self.event = ev     # [midi ch, note, velocity, duration]
        self.during_noteon = False
        self.destroy = False
        self.off_msr = 0
        self.off_tick = 0

    def _note_off(self):
        self.destroy = True
        self.during_noteon = False
        # midi note off
        self.md.send_midi_note(self.event[0], self.event[1], 0)

    def periodic(self,msr,tick):
        if not self.during_noteon:
            self.during_noteon = True
            tk = self.parent.get_tick_for_onemsr()
            self.off_msr = msr
            self.off_tick = tick + self.event[3]
            while self.off_tick > tk:
                self.off_tick -= tk
                self.off_msr += 1
            # midi note on
            self.md.send_midi_note(self.event[0], self.event[1], self.event[2])
        else:
            if msr == self.off_msr and tick > self.off_tick:
                self._note_off()

    def destroy_me(self):
        return self.destroy

    def stop(self):
        if self.during_noteon:
            self._note_off()
