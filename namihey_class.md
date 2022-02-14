# Namihey design

## Class Design

```plantuml
@startuml
:Parsing
@enduml
```

### Parsing
- File: namiparse.py
- Role: 入力コマンドのパース処理

### Seq
- File: namiseq.py
- Role: 複数ブロックの管理
- Note:
    - def _calc_max_measure():
        - この中で、各パートの return_to_top() をコールし、各パートの最大tickから最大小節数を算出
    - def periodic()
        - generate_ev() から呼ばれ続ける別スレッドの関数

### Block
- File: namiseq.py
- Role: ブロックの Super Class

### BlockRegular
- File: namiseq.py
- Role: 各パートが同期したループを持つ普通のブロック

### BlockIndependentLoop
- File: namiseq.py
- Role: 各パートが独立したループを持つブロック

### Part
- File: namipart.py
- Role: パート内の、シーケンスデータ生成オブジェクトによるデータ生成と、再生コントロール
- Note:
    - Part IF を提供し、シーケンスの生成オブジェクトをコール
    - シーケンス生成オブジェクトには、oneByOne と atOnce の2typeがある

### PartGenPlay
- File: namiptgen.py
- Role: ユーザーが入力したデータから、その場で MIDI シーケンスを生成し、再生コントロールするオブジェクト(atOnce型)
- Note:
    - 実際には、内部で PhraseGenerator オブジェクトを呼び出して、このオブジェクトにシーケンスを作ってもらう

### PhraseGenerator
- File: namiphrase.py
- Role: 入力データから MIDI シーケンスを生成する処理
- Note:
    - PartGen からコールされる

### PatternGenerator
- File: namipattern.py
- Role: ユーザーが入力したデータをもとに、再生時に逐次シーケンスを生成し、再生コントロールするオブジェクト(oneByOne型)
    - Random 型と Arpeggio 型の二つのタイプがある

### NamiGui
- File: namigui.py
- Role: pygame を用いて、別windowによる各種情報の表示を行う

### Log
- File: namilib.py
- Role: デバッグ用のログ書き出しサービスを提供する
    - nlib.log.record(文字列) を書けば、時間情報込みで log.txt に出力される


---------------

## Thread


### Main Thread
- Main Loop: NamiGui(): main_loop()
- Role: pygame GUI の表示


### Cui Thread
- Main Loop: namihey.py: cui()
- Role: コンソールでの Keyboard 入力受付とCUI表示

### Event Generator Thread
- Main Loop: namihey.py: generate_ev()
- Role: MIDI 出力用の周期処理