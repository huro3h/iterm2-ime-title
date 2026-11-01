#!/bin/bash
# iterm2-ime-title のセットアップ。
# iTerm2 の AutoLaunch フォルダに ime_title.py へのシンボリックリンクを張る。
# コピーではなくリンクにするのは、git pull だけで更新を反映できるようにするため。
#
# 使い方:
#   ./setup.sh              リンクを張る(何度実行しても安全)
#   ./setup.sh --uninstall  自分が張ったリンクだけを消す

set -eu

SCRIPT="$(cd "$(dirname "$0")" && pwd)/ime_title.py"
AUTOLAUNCH="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
LINK="$AUTOLAUNCH/ime_title.py"

if [ "${1:-}" = "--uninstall" ]; then
  # 同名の別物を巻き込まないよう、このリポジトリを指すリンクのときだけ消す
  if [ -L "$LINK" ] && [ "$(readlink "$LINK")" = "$SCRIPT" ]; then
    rm "$LINK"
    echo "削除しました: $LINK"
    echo "動いているスクリプトは iTerm2 を再起動するまで残ります"
  else
    echo "このリポジトリのリンクはありません: $LINK"
  fi
  exit 0
fi

if [ -e "$LINK" ] && [ ! -L "$LINK" ]; then
  echo "error: リンクではないファイルが既にあります。確認して退けてから再実行してください: $LINK" >&2
  exit 2
fi

mkdir -p "$AUTOLAUNCH"
ln -sfn "$SCRIPT" "$LINK"
echo "リンクしました: $LINK -> $SCRIPT"

if [ "$(defaults read com.googlecode.iterm2 EnableAPIServer 2>/dev/null)" != "1" ]; then
  echo
  echo "注意: iTerm2 の Python API が有効になっていません。"
  echo "  Settings > General > Magic > Enable Python API をオンにしてください。"
fi

cat <<'NEXT'

残りの手順(README の「セットアップ」も参照):
  1. Scripts > Manage > Install Python Runtime(未導入の場合)
  2. Scripts > AutoLaunch > ime_title.py で起動(次回からは iTerm2 の起動時に自動で動く)
  3. Settings > Profiles > General > Title で「入力モード付きタイトル」を選ぶ
NEXT
