# 抽出記録

ゲーム開発リポジトリ内の以下のコードを出発点としています。

| 抽出元 | 独立版 |
| --- | --- |
| `tools/repository_audit.py` | `tools/repository_audit.py` |
| `tools/tests/test_repository_audit.py` | `tools/tests/test_repository_audit.py` |

既存の検出ロジックを保持し、対象リポジトリを CLI 引数から指定できるよう変更しました。警告でも失敗するモードと、ゲームに依存しない説明・設定を追加しています。ゲームデータ・素材・ローカルパス・過去の履歴はコピーしていません。元のゲーム側のスクリプトは削除・変更せず残しています。
