---
name: iterm2-ime-title
description: iterm2-ime-title(iTerm2 のタイトルに入力モードを出す Python API スクリプト)を改修・調査するときに使う。仕組み、却下した実装案、iTerm2 API のハマりどころ、動作確認の手順をまとめている。
---

# iterm2-ime-title

## ファイル構成

| ファイル | 役割 |
|---|---|
| `ime_title.py` | 本体。iTerm2 の AutoLaunch から起動される常駐スクリプト |
| `setup.sh` | AutoLaunch へのシンボリックリンクを張る/消す |

AutoLaunch はコピーではなくリンクにしている。`git pull` だけで更新を反映できるようにするため。
作者の手元では dotfiles の `bootstrap.sh` がこのリポジトリを `~/projects` に clone して `setup.sh` を呼ぶ。

## 仕組み

1. **タイトルプロバイダ** `ime_title`(`@iterm2.TitleProviderRPC`)を識別子 `com.huro3h.ime-title` で登録する。
   引数に `user.ime?` `path?` の変数を参照させているので、どちらかが変わると iTerm2 が呼び直す。
   `path` はシェル統合が cd のたびに送るディレクトリ。ホーム以下は `~` に縮めて出す。
2. 各セッションのユーザー変数 `user.ime` に `A` / `あ` / `ア` を書く。タイトルの組み立ては iTerm2 側に任せる。
3. 入力ソースは Carbon の `TISCopyCurrentKeyboardInputSource` を ctypes で呼んで 30ms ごとに読む。
4. ⌘の単押しを `KeystrokeMonitor(advanced=True)` の flags-changed で検出し、先回りして表示を変える。

**識別子 `com.huro3h.ime-title` は変えない。** プロファイルの Title 設定がこの識別子で関数を探すため、
変えると全員のタイトル設定がやり直しになる。表示名(「入力モード付きタイトル」)は変えてもよい。

## 却下した実装案

- **バッジに出す**(最初の版): iTerm2 のバッジは最大幅・最大高さの枠いっぱいまで文字を拡大するので、
  「かな」のような短い文字列だと巨大になる。`set_badge_max_width/height` で縮められるが、本文に被るのは変わらない。
- **スクリプトからタイトル設定まで行う**: `LocalWriteOnlyProfile.set_title_function()` を
  `session.async_set_profile_properties()` で送ると、iTerm2 3.7.6 は `REQUEST_MALFORMED` を返す
  (表示名を ASCII にしても同じ。`set_title_components` だけなら通る)。起動直後にこれで例外終了していた。
  そのためタイトルの選択は設定画面での手作業にしている。
- **入力ソース切り替えの通知で即時更新**: 分散通知
  `com.apple.Carbon.TISNotifySelectedKeyboardInputSourceChanged` は、別スレッドで `CFRunLoopRun` しても届かない
  (メインスレッドで登録して run loop を回せば約2msで届く)。結局メインスレッドで定期的に run loop を回すことになり、
  ポーリングと変わらないので採らなかった。

## ハマりどころ

- **`TISCopyCurrentKeyboardInputSource` は run loop を回さないと古い値を返し続ける。** 長く動くプロセスでは
  切り替えの通知を受け取れずキャッシュが更新されない。読む前に `CFRunLoopRunInMode(..., 0, True)` を呼んでいる。
- **`Keystroke.keycode` は `Keycode` 列挙に無い値で `ValueError` になる。** 英数(0x66)・かな(0x68)キーは列挙に無い。
  keycode を読むのは flags-changed(修飾キーは全部列挙にある)のときだけにしている。
- **先回り直後のちらつき。** ⌘を離した時点では入力ソースがまだ変わっていないことがあり、ポーリングが古い値で
  表示を戻してしまう。先回り後 `TAP_HOLD_SECONDS`(0.5秒)はポーリング結果が表示と食い違っても無視し、
  それを過ぎたら実際の状態に合わせる。
- **⌘の単押し判定は Karabiner の設定と揃える。** 「押して、ほかのキーを挟まず、`COMMAND_TAP_SECONDS` 以内に離した」。
  ほかの修飾キーの変化も挟んだら単押し扱いしない。Karabiner の設定がない環境では誤表示になるので
  `COMMAND_TAP_ENABLED = False` で切れるようにしてある。

## 動作確認

AutoLaunch のスクリプトは iTerm2 の中で動くので、ターミナルから直接見えない。

- 起動しているか: `pgrep -fl "python.*ime_title"`
- 起動/再起動: `pkill -f "python.*AutoLaunch/ime_title.py"` のあと
  `osascript -e 'tell application "iTerm2" to launch API script named "ime_title.py"'`。
  **改名直後は iTerm2 がスクリプト一覧を更新するまで `Script not found` になる**ので、メニューから起動してもらう。
- エラーで止まる原因を見る: iTerm2 の Python で直接実行するとトレースバックが出る(iTerm2 に接続できる)。
  `"$HOME/Library/Application Support/iTerm2/uv/venvs/3.12/bin/python" ime_title.py`
  (runtime のパスは iTerm2 のバージョンで変わる)。
- 表示の確認: 同じ Python で `app.terminal_windows` → `tab.sessions` を回し、
  `async_get_variable("user.ime")` と `async_get_variable("name")`(計算後のタイトル)を読む。
  入力の切り替え自体はこちらからは行えないので、ユーザーに切り替えてもらってから読む。
