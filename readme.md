
# namihey Alpha-version

## about namihey

    namihey is a music description language developed mainly for use in Live Coding.
    The main feature of namihey is the ability to specify tones by a gradation with a movable-do.
    It is written in python and output to MIDI by the mido library.



## namihey とは

    namihey は、主に Live Coding で使うために開発された音楽記述言語です。
    音の指定を、移動ドによる階名で指定することを大きな特徴とします。
    python によって記述され、mido というライブラリにより、MIDI出力します。



## 記述の基本ルール

- 起動
    - 'python namihey.py'  : 通常の python スクリプトと同じ
- 入力
    - '[1]~~> ' : nami prompt
        - [1]は、part 1の入力状態であることを示す
        - このプロンプトの後に、コマンドやフレーズを書き込む
    - カーソルによる過去入力のヒストリー呼び出しが可能
- 終了
    - 'quit' で終了

## フレーズ追加

- [*note*][*duration*][*velocity*] : フレーズ追加の基本形式
    - *note*: 階名
    - *duration*: 音価
    - *velocity*: 音量
    - [*duration*] と [*velocity*] は省略可能
    - [] : 全データ削除

- 階名表現
    - d,r,m,f,s,l,t: ド、レ、ミ、ファ、ソ、ラ、シ
    - di,ri,fi,si,li: ド#、レ#、ファ#、ソ#、ラ#
    - ra,ma,sa,lo,ta: レb、ミb、ソb、ラb、シb
    - -d : 1オクターブ下のド、 +d : 1オクターブ上のド
    - ',' '|' : カンマ、縦棒、どちらで区切っても良い
    - x: 休符
    - d=m=s, : 同時演奏
    - |:d,r,m:3| : ドレミを３回演奏（数字がなければ1回繰り返し）

- 音価表現
    - [1,1,1,1:8] : 八分音符を４回
    - [1,1,1,1] : 四分音符を４回（:n を省略すると四分音符になる）
    - [2,1,2,1,3:12] : 一拍3連(12分音符)で、タータタータター
    - 音価を省略した場合、全て四分音符とみなす

- 音量表現
    - [127,127,127,127] : MIDI velocity=127 を４回
    - [ff,f,mf,mp,p,pp] : ff-pp で音量を表現できる        【未実装】
    - 省略した場合、全て velocity=100 とみなす

- フレーズ関連コマンド
    - 'copyto 2' : 入力中のpartのフレーズを part2 にコピー
    - 'input 1' : part 1への入力切り替え（1〜16)

## 再生コントロール

- 'play' : シーケンス開始
- 'mute 2,3' : part2 と part3 をミュートする        【未実装】
- 'mutecancel' : ミュートしていたパートのミュート解除する    【未実装】
- 'fine' : ブロックの最後でシーケンス終了
- 'stop' : 直ちにシーケンス終了

## 設定コマンド

- 'set bpm=100' : BPM（テンポ）=100 にセット
- 'set beat=4/4' : 拍子を 4/4 にセット
- 'set key=C4' : key を C4 にセット
    - namihey にとって key とは [d] と指示されたときの音名を表す
    - デフォルト値は C4
    - 入力中の part に対してのみ効果
- 再生中でも設定可能。再生中の場合、次のループから反映される

## 音を出す方法

- MIDI 音源を繋ぐ
- Logic などマルチパートで MIDI受信するアプリを同時に起動する

