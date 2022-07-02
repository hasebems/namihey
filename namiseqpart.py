# -*- coding: utf-8 -*-
import namilib as nlib
import namiphrase as nph
import namiseqply as sqp
import namiseqptn as ptnlp
import namiseqphr as phrlp

####
#   起動時から存在し、決して destroy されない SeqPlay Obj.
class SeqPart(sqp.SeqPlay):

    def __init__(self, obj, md, fl, num):
        super().__init__(obj, md, 'Part')
        self.part_num = num
        self.first_measure_num = 0 # 新しい Phrase/Pattern が始まった絶対小節数

        self.fl = fl
        self.loop_obj = None
        self.keynote = nlib.DEFAULT_NOTE_NUMBER
        self.seq_type = None
        self.description = [None for _ in range(3)]
        self.loop_measure = 0   # whole_tick と同時生成
        self.whole_tick = 0     # loop_measure と同時生成
        self.state_reserve = False
        self.elm = None     # 再生用の要素が入ったオブジェクト

    def _generate_sequence(self):
        tick_for_onemsr = self.parent.get_tick_for_onemsr()
        if self.seq_type == 'phrase':
            pg = nph.PhraseGenerator(self.description, self.keynote)
            self.whole_tick, self.elm = pg.convert_to_MIDI_like_format()
            # その時の beat 情報で、whle_tick を loop_measure に換算
            self.loop_measure = self.whole_tick//tick_for_onemsr + \
                (0 if self.whole_tick%tick_for_onemsr == 0 else 1)
            return True
        elif self.seq_type == 'random':
            self.elm = ptnlp.PatternGenerator(True,self.description)
            if self.elm != None:
                self.loop_measure = self.elm.max_measure_num
                self.whole_tick = self.loop_measure*tick_for_onemsr
                return True
        elif self.seq_type == 'arp':
            self.elm = ptnlp.PatternGenerator(False,self.description)
            if self.elm != None:
                self.loop_measure = self.elm.max_measure_num
                self.whole_tick = self.loop_measure*tick_for_onemsr
                return True
        return False

    def _generate_loop(self,msr):
        if self.seq_type == 'phrase':
            self.loop_obj = phrlp.PhraseLoop(self.parent, self.md, msr, self.elm,  \
                self.keynote, self.part_num, self.whole_tick)
        elif self.seq_type == 'random' or self.seq_type == 'arp':
            self.loop_obj = ptnlp.PatternLoop(self.parent, self.md, msr, self.elm,  \
                self.keynote, self.part_num)
        self.parent.add_sqobj(self.loop_obj)

    def _set_chain_loading(self, msr, elapsed_msr):
        if msr == 0:
            noteinfo = self.fl.read_first_chain_loading(self.part_num)
            #self.add_seq_description(noteinfo)
            self.seq_type = noteinfo[0]
            self.description = noteinfo[1:]
            return True
        else:
            # 次回が overlap 対象か？
            ol = self.fl.get_overlap(self.part_num)
            # あるいは、ひとつ前のデータに中身が無ければ
            # 1小節前になったか？ overlap の場合２小節前になったか？
            condition = \
                (self.loop_measure == 0) or \
                ((self.loop_measure == elapsed_msr) and not ol) or \
                ((self.loop_measure-1 == elapsed_msr) and ol)
            if condition:
                # wait_for_looptop 期間中に次の Description をセットする
                noteinfo = self.fl.read_next_chain_loading(self.part_num)
                self.seq_type = noteinfo[0]
                self.description = noteinfo[1:]
                return True
            return False

    ## Seqplay thread内でコール
    def start(self):
        self.first_measure_num = 0

    def msrtop(self,msr):
        def new_loop(msr):
            if self._generate_sequence():
                # 新たに Loop Obj.を生成
                self._generate_loop(msr)
            self.first_measure_num = msr    # 計測開始の更新

        elapsed_msr = msr - self.first_measure_num
        if self.fl.chain_loading_state:
            # Chain Loading
            if self._set_chain_loading(msr, elapsed_msr):
                new_loop(msr)

        elif self.state_reserve:
            self.state_reserve = False
            # 前小節にて phrase/pattern 指定された時
            if msr == 0:
                # 今回 start したとき
                new_loop(msr)

            elif self.loop_measure == 0:
                # データのない状態で start し、今回初めて指定された時
                new_loop(msr)

            elif self.loop_measure != 0 and elapsed_msr%self.loop_measure == 0:
                # 前小節にて Loop Obj が終了した時
                new_loop(msr)

            else:
                # 現在の Loop Obj が終了していない時
                pass

        elif self.elm != None and \
            self.loop_measure != 0 and elapsed_msr%self.loop_measure == 0:
            # 同じ Loop.Obj を生成する
            self._generate_loop(msr)

        else:
            # Loop 途中で何も起きないとき
            pass

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
            self.md.send_control(self.part_num, cc_num, val)

    def change_pgn(self, pgn):
        self.md.send_program(self.part_num, pgn)

    def add_seq_description(self, data):
        self.seq_type = data[0]
        self.description = data[1:]
        self.state_reserve = True
