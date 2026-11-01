# Changelog

このプロジェクトの主な変更点を記録します。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠し、
バージョニングは [セマンティック バージョニング](https://semver.org/lang/ja/) を採用しています。

新しいバージョンを上に追記します。未リリースの変更は `[Unreleased]` にためていき、
リリース時にバージョン番号と日付へ繰り上げます。

## [Unreleased]

### Changed
- 入力モードのあとに、「セッション名 (ジョブ名)」の代わりに現在のディレクトリを出すようにした。ホーム以下は `~` に縮める。

## [1.0.0] - 2026-11-01

### Added
- iTerm2 のタイトルの先頭に、いまの入力モード(🔵A / ⚪あ / ⚪ア)を表示する。全ウィンドウ・全タブ・全ペインが一斉に切り替わる。
- Karabiner-Elements で⌘の単押しを英数/かなキーにしている場合に、入力ソースの切り替えを待たずに表示を変える。使わない環境では `COMMAND_TAP_ENABLED = False` で切れる。
- `setup.sh` で iTerm2 の AutoLaunch にリンクを張り、iTerm2 の起動時に自動で動くようにする。`--uninstall` で外せる。
