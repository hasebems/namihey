# -*- coding: utf-8 -*-
import namilib as nlib

class SeqPlay:

    def __init__(self, obj, md, type):
        self.parent = obj
        self.md = md
        self.type = type

    def start(self):
        pass

    def stop(self):
        pass

    def fine(self):
        pass

    def msrtop(self):
        pass

    def periodic(self,msr,tick):
        pass

    def destroy_me(self):
        return False

class Part(SeqPlay):

    def __init__(self, obj, md, num):
        super().__init__(obj, md, 'Part')
        self.part_num = num
        self.count = 0

    def _set_note(self,ev):
        obj = Note(self.parent, self.md, ev)
        self.parent.add_sqobj(obj)

    def start(self):
        self.count = 0

    def periodic(self,msr,tick):
        if self.part_num != 0:
            return
        # example for generating Note Event
        cnt = self.count
        if msr == (cnt//4) and tick > (cnt%4)*480:
            note = cnt%12
            self.count += 1
            self._set_note([self.part_num,0x3c+note,0x7f,600])

    def destroy_me(self):
        return False


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
