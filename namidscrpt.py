# -*- coding: utf-8 -*-

class Description:

    def complement_bracket(self, input_text):
        # [] のセットを抜き出し、中身を note_info に入れる
        note_info = []
        tx = input_text
        while True:
            num = tx.find(']')
            if num == -1:
                break
            note_info.append(tx[1:num])
            tx = tx[num + 1:].strip()
            if len(tx) == 0:
                break
            if tx[0:1] != '[':
                break

        # [] の数が 1,2 の時は中身を補填
        bracket_num = len(note_info)
        if bracket_num == 1:
            note_info.append('1')  # set default value
            note_info.append('100')
        elif bracket_num == 2:
            note_info.append('100')  # set default velocity value
        elif bracket_num == 0 or bracket_num > 3:
            # [] の数が 1〜3 以外ならエラー
            return None

        note_info.insert(0, 'phrase')
        return note_info

    def complement_brace(self, input_text):
        # {} のセットを抜き出し、中身を note_info に入れる
        note_info = []
        dialogue = ''
        tx = input_text
        while True:
            num = tx.find('}')
            if num == -1:
                break
            note_info.append(tx[1:num])
            tx = tx[num + 1:].strip()
            if len(tx) == 0:
                break
            if tx[0:1] != '{':
                break

        # [] の数が 1,2 の時は中身を補填
        brktNum = len(note_info)
        if brktNum == 1:
            note_info.append('1')  # set default value
            note_info.append('100')
        elif brktNum == 2:
            note_info.append('100')  # set default velocity value
        elif brktNum == 0 or brktNum > 3:
            # [] の数が 1〜3 以外ならエラー
            return None,"what?"

        if note_info[0][0:3] == 'rnd':
            note_info.insert(0, 'random')
            dialogue = "set Random Pattern!"
        elif note_info[0][0:3] == 'arp':
            note_info.insert(0, 'arp')
            dialogue = "set Arpeggio Pattern!"
        else:
            return None,"what?"
        return note_info, dialogue

    def set_dscrpt_to_block(self, part_num, blk, dscrpt):
        # complement_bracket/brace で note_info[] を得た後に txt に入れて呼ばれる
        blk.part(part_num).clear_description()
        blk.part_in_advance(part_num).add_seq_description(dscrpt)

    def set_dscrpt_to_seq2(self, part_num, sq2, dscrpt):
        # complement_brace で note_info[] を得た後に txt に入れて呼ばれる
        #sq2.get_part(part_num).clear_description()
        sq2.get_part(part_num).add_seq_description(dscrpt)