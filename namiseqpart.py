# -*- coding: utf-8 -*-
import namilib as nlib
import namiseqply as sqp
import namiseqptn as ptnlp

####
#   起動時から存在し、決して destroy されない SeqPlay Obj.
class SeqPart(sqp.SeqPlay):

    def __init__(self, obj, md, num):
        super().__init__(obj, md, 'Part')
        self.part_num = num
        self.first_measure_num = -1 # その Phrase/Pattern が始まった小節数

        self.loop_obj = None
        self.keynote = nlib.DEFAULT_NOTE_NUMBER
        self.description = [None for _ in range(4)]
        self.loop_measure = 0
        self.state_reserve = False
        self.elm = None     # 再生用の要素が入ったオブジェクト

    def _generate_loop(self):
        if self.part_num != 0: return # とりあえず part1 のみ
        self.loop_obj = ptnlp.PatternLoop(self.parent, self.md, self.elm, self.keynote)
        self.parent.add_sqobj(self.loop_obj)

    def _generate_sequence(self):
        seq_type = self.description[0]
        if seq_type == 'phrase':
            #self.whole_tick = self.ptgen.set_phrase(self.description[1:], self.keynote)
            self.loop_measure = 0
            pass
        elif seq_type == 'random':
            self.elm = ptnlp.PatternGenerator(True,self.description[1:])
        elif seq_type == 'arp':
            self.elm = ptnlp.PatternGenerator(False,self.description[1:])

    ## Seqplay thread内でコール
    def start(self):
        self.first_measure_num = -1

    def msrtop(self,msr):
        if self.first_measure_num == -1:    # 計測開始
            self.first_measure_num = msr

        if self.state_reserve:
            # pattern 変更イベント時
            self._generate_sequence()
            if self.elm != None:
                self.loop_measure = self.elm.max_measure_num
            self.state_reserve = False
            self.first_measure_num = msr    # 計測開始の更新

        # 計測開始からの経過小節数
        elapsed_msr = msr - self.first_measure_num

        # Loop分の長さを過ぎたら、新たに Loop Obj.を生成
        if self.elm != None and \
           self.loop_measure != 0 and \
           elapsed_msr%self.loop_measure == 0:
            self._generate_loop()

    #def periodic(self,msr,tick):
    #    pass

    def destroy_me(self):
        return False    # 最後まで削除されない

    #def stop(self):
    #    pass

    #def fine(self):
    #    self.stop()

    ## CUI thread内でコール
    def change_keynote(self, nt):
        self.keynote = nt
        self.state_reserve = True

    def change_cc(self, cc_num, val):
        if val >= 0 and val < 128:
            self.volume = val
            self.md.send_control(self.midich, cc_num, val)

    #def clear_description(self):
    #    self.add_seq_description(['phrase',None,None,None])

    def add_seq_description(self, data):
        self.description = data
        self.state_reserve = True


