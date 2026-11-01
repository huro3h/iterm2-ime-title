# iterm2-ime-title

iTerm2 のタイトルの先頭に、いまの日本語入力のモードを表示する Python API スクリプト。

```
🔵A Default (zsh)     ← 英字
⚪あ Default (zsh)    ← ひらがな
⚪ア Default (zsh)    ← カタカナ
```

ターミナルで入力を始めてから、かなのままだったと気づいて打ち直すのを防ぐために作った。
バッジ(画面右上に重ねる大きな文字)と違って本文に被らず、どのタブにいても目に入る。

## 主な機能

- 入力ソースを 30ms ごとに確認し、全ウィンドウ・全タブ・全ペインのタイトルを一斉に切り替える
- タイトルの残りは iTerm2 の既定と同じ「セッション名 (ジョブ名)」の形を保つ
- **⌘キーの単押しに先回りして表示を変える**(任意)。Karabiner-Elements で
  「⌘を単体で押したら英数/かなキーを送る」設定にしている場合、同じ判定をして
  入力ソースの切り替えを待たずに表示を変える(左⌘ = 英字、右⌘ = かな)
- Google日本語入力とmacOS標準の日本語入力のどちらでも動く

## 動作環境

- macOS
- iTerm2 3.7 以降(3.7.6 で確認)
- 追加のパッケージは不要。iTerm2 が用意する Python Runtime だけで動く

## セットアップ

```bash
git clone https://github.com/huro3h/iterm2-ime-title.git
cd iterm2-ime-title
./setup.sh
```

`setup.sh` は iTerm2 の AutoLaunch フォルダ(`~/Library/Application Support/iTerm2/Scripts/AutoLaunch/`)に
`ime_title.py` へのシンボリックリンクを張る。リンクなので、更新は `git pull` だけで済む。

続けて iTerm2 側で次の3つを行う。

1. **Python API を有効にする**: Settings > General > Magic > **Enable Python API** をオン
   (`setup.sh` が無効を検出したら知らせる)
2. **Python Runtime を入れる**: Scripts > Manage > **Install Python Runtime**(未導入の場合だけ)
3. **スクリプトを起動して、タイトルに選ぶ**
   1. Scripts > AutoLaunch > **ime_title.py** を選んで起動する。次回からは iTerm2 の起動時に自動で動く
   2. Settings > Profiles > (使っているプロファイル) > General > **Title** で
      **「入力モード付きタイトル」** を選ぶ

タイトルの選択肢は、スクリプトが動いている間しか一覧に出ない。見当たらなければ手順 3-1 をやり直す。
プロファイルが複数あるなら、表示したいプロファイルごとに選ぶ。

### Karabiner-Elements を使っていない場合

⌘キーへの先回りは、⌘の単押しで英数/かなに切り替わる前提で動く。その設定がないと、
⌘を単独で押すたびに表示が一瞬だけ変わって戻る。`ime_title.py` の冒頭を次のように変えて切る。

```python
COMMAND_TAP_ENABLED = False
```

切っても、入力ソースの確認(30ms ごと)で表示は追従する。

## カスタマイズ

`ime_title.py` の冒頭の定数を書き換えて、Scripts > AutoLaunch > ime_title.py で起動し直す。

| 定数 | 既定値 | 内容 |
|---|---|---|
| `IME_MARKS` | `{"あ": "⚪", "ア": "⚪", "A": "🔵"}` | 入力モードごとに前に付ける記号。タイトルの文字そのものには色を付けられないので、色付きの絵文字で見分ける |
| `COMMAND_TAP_ENABLED` | `True` | ⌘キーへの先回りを使うか |
| `COMMAND_TAP_SECONDS` | `1.0` | ⌘を押してから離すまで、単押しとみなす時間。Karabiner の `to_if_alone` のタイムアウトと揃える |
| `POLL_SECONDS` | `0.03` | 入力ソースを確認する間隔(秒) |

## 更新・削除

```bash
git pull                 # 更新。Scripts > AutoLaunch > ime_title.py で起動し直すと反映される
./setup.sh --uninstall   # AutoLaunch のリンクを消す
```

削除したら、プロファイルの Title も別の項目に戻しておく。

## 制限

- **スクリプトが止まっている間は、タイトルが空になることがある。** タイトルを作る関数がスクリプト側にあるため。
  iTerm2 の起動時に自動で動くので、普段は気にしなくてよい。止まったときは Scripts > Manage > Console でエラーを確認できる
- タイトルの選択は手作業になる。API からセッションごとに設定しようとすると iTerm2 に拒否される
  (`REQUEST_MALFORMED`)ため、設定画面で一度だけ選ぶ形にしている
- ⌘キーへの先回りは、iTerm2 が前面にあるときだけ働く。ほかのアプリで切り替えた場合は、入力ソースの確認で追従する

## ライセンス

[MIT](LICENSE)
