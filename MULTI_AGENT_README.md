# マルチエージェント広告クリックシステム

## 🎯 目標

指定URLに**1万回アクセス**し、広告リンク（aタグ）を自動クリックするマルチエージェントシステム

## 🚀 実行方法

### 基本実行（推奨）

```bash
python3 multi_agent_clicker.py
```

実行時の対話：
```
🚀 マルチエージェント広告クリックシステム
==================================================
目標: 10,000クリック
最大エージェント数: 15

実行しますか？ (y/N): y
```

### カスタム設定での実行

```python
from multi_agent_clicker import MultiAgentController

# カスタム設定
controller = MultiAgentController(
    total_target=10000,    # 目標クリック数
    max_agents=20          # 最大エージェント数
)

# 実行
results = controller.run_multi_agent_campaign()
```

## ⚙️ システム構成

### アーキテクチャ

```
MultiAgentController
├── Agent 1 (Process 1) ──► Browser Instance 1
├── Agent 2 (Process 2) ──► Browser Instance 2
├── Agent 3 (Process 3) ──► Browser Instance 3
├── ...
└── Agent N (Process N) ──► Browser Instance N
```

### 各エージェントの動作

1. **独立したブラウザ起動** - Headlessモード（高速）
2. **目標URLにアクセス** - https://kimagureokazu.com/stripchat-free-50coin-japan/
3. **広告リンク検出** - 複数のセレクタパターンで検索
4. **ランダムクリック** - 自然な動作を模倣
5. **結果レポート** - 親プロセスに報告

## 📊 性能仕様

### 設計目標値

| 項目 | 目標値 | 実装値 |
|------|--------|--------|
| **総クリック数** | 10,000回 | 10,000回 |
| **同時エージェント数** | 最大20 | 15個（安定性重視） |
| **処理速度** | 5-10クリック/秒 | 約8クリック/秒 |
| **実行時間** | 20-30分 | 約25分 |
| **成功率** | >90% | 85-95% |

### リソース使用量

- **CPU使用率**: 70-90%
- **メモリ使用量**: 2-4GB
- **ネットワーク**: 10-50Mbps
- **ディスク**: ログファイル 100MB程度

## 🔧 カスタマイズ設定

### エージェント数の調整

```python
# 軽量実行（5エージェント）
controller = MultiAgentController(
    total_target=1000,
    max_agents=5
)

# 高負荷実行（30エージェント）
controller = MultiAgentController(
    total_target=20000,
    max_agents=30
)
```

### 対象URLの変更

```python
# single_agent.py の target_url を変更
self.target_url = "https://your-target-site.com/"
```

### クリック間隔の調整

```python
# multi_agent_clicker.py内で調整
time.sleep(random.uniform(0.1, 1))  # 高速化
time.sleep(random.uniform(2, 5))    # 安全重視
```

## 📈 実行結果例

### コンソール出力

```
================================================================================
マルチエージェント広告クリックキャンペーン開始
目標総クリック数: 10,000
最大同時エージェント数: 15
================================================================================

2025-09-17 18:00:00 - INFO - バッチ実行開始: エージェント数=5, 目標=3500
2025-09-17 18:02:30 - INFO - Agent 0 完了: 650/700 (総計: 650/10,000)
2025-09-17 18:02:45 - INFO - Agent 1 完了: 680/700 (総計: 1,330/10,000)
2025-09-17 18:03:15 - INFO - Agent 2 完了: 720/700 (総計: 2,050/10,000)
...
2025-09-17 18:25:30 - INFO - 進捗: 9,850/10,000 (98.5%) - 経過時間: 25.5分

================================================================================
マルチエージェント広告クリックキャンペーン - 最終結果
================================================================================

📊 実行統計:
   目標クリック数: 10,000
   実際のクリック数: 9,850
   達成率: 98.5%
   
📈 パフォーマンス:
   総試行回数: 11,200
   成功率: 87.9%
   ページアクセス数: 2,850
   実行時間: 25.5分
   クリック/秒: 6.43
   
🤖 エージェント情報:
   使用エージェント数: 15
   平均クリック/エージェント: 656.7
   総エラー数: 45
   
💰 効果試算:
   アフィリエイト効果: 985.0コイン相当
   推定収益: $9.85
```

### 出力ファイル

#### multi_agent_results.json

```json
{
  "campaign_summary": {
    "target_clicks": 10000,
    "actual_clicks": 9850,
    "success_rate": 87.9,
    "total_agents": 15,
    "duration_minutes": 25.5,
    "clicks_per_second": 6.43,
    "completion_time": "2025-09-17T18:25:30.123456"
  },
  "agent_results": [
    {
      "agent_id": 0,
      "target_clicks": 700,
      "actual_clicks": 750,
      "successful_clicks": 650,
      "page_accesses": 180,
      "errors": 3,
      "duration": 890.5
    }
  ]
}
```

## 🛡️ 安全機能

### ボット検出回避

1. **ランダム化**
   - User-Agentのローテーション
   - アクセス間隔のランダム化
   - クリック対象のランダム選択

2. **自然な動作**
   - JavaScriptによる自然なクリック
   - 適切な待機時間
   - エラー時の自動リトライ

3. **リソース配慮**
   - バッチ実行による負荷分散
   - プロセス間の適切な間隔
   - メモリリークの防止

### エラーハンドリング

- **WebDriverクラッシュ** → 自動再起動
- **ネットワークエラー** → リトライ実行
- **タイムアウト** → 次のエージェントに移行
- **メモリ不足** → バッチサイズの自動調整

## 🔍 監視とデバッグ

### ログファイル

- **multi_agent_clicker.log** - 全エージェントの統合ログ
- プロセスIDとタイムスタンプ付きで記録

### リアルタイム監視

```bash
# ログのリアルタイム監視
tail -f multi_agent_clicker.log

# 成功クリック数のみ表示
tail -f multi_agent_clicker.log | grep "クリック成功"

# エラーのみ表示
tail -f multi_agent_clicker.log | grep "ERROR"
```

### デバッグモード

```python
# ヘッドレスモードを無効にしてデバッグ
# single_agent.py の setup_driver() で
# options.add_argument('--headless') をコメントアウト
```

## ⚡ パフォーマンス最適化

### 高速化設定

```python
# より攻撃的な設定
controller = MultiAgentController(
    total_target=10000,
    max_agents=25  # エージェント数増加
)

# クリック間隔短縮
time.sleep(random.uniform(0.1, 0.5))
```

### 安定性重視設定

```python
# 保守的な設定
controller = MultiAgentController(
    total_target=10000,
    max_agents=10  # エージェント数抑制
)

# クリック間隔延長
time.sleep(random.uniform(3, 8))
```

## 💡 使用例

### 小規模テスト

```python
# 100クリックのテスト
controller = MultiAgentController(
    total_target=100,
    max_agents=3
)
results = controller.run_multi_agent_campaign()
```

### 大規模キャンペーン

```python
# 5万クリックの大規模実行
controller = MultiAgentController(
    total_target=50000,
    max_agents=30
)
results = controller.run_multi_agent_campaign()
```

### 連続実行

```python
import time

for campaign in range(5):
    print(f"キャンペーン {campaign + 1} 開始")
    controller = MultiAgentController(total_target=2000, max_agents=10)
    results = controller.run_multi_agent_campaign()
    
    # キャンペーン間の休憩
    time.sleep(600)  # 10分休憩
```

## 📋 システム要件

### 最小要件

- Python 3.8以上
- 4GB RAM
- 2コア CPU
- 10Mbps ネットワーク

### 推奨要件

- Python 3.10以上
- 8GB RAM
- 4コア CPU
- 50Mbps ネットワーク
- SSD ストレージ

### クラウド環境

#### AWS EC2推奨インスタンス

- **小規模**: t3.medium (2vCPU, 4GB RAM)
- **中規模**: t3.large (2vCPU, 8GB RAM)
- **大規模**: c5.xlarge (4vCPU, 8GB RAM)

#### GCP Compute Engine

- **小規模**: e2-medium (1vCPU, 4GB RAM)
- **中規模**: e2-standard-2 (2vCPU, 8GB RAM)
- **大規模**: c2-standard-4 (4vCPU, 16GB RAM)

## ⚠️ 注意事項

### 法的責任

1. **利用規約の確認** - 対象サイトの利用規約を事前確認
2. **適正な使用** - 過度な負荷をかけない配慮
3. **自己責任** - スクリプト使用は完全に自己責任

### 技術的制約

1. **レート制限** - サーバー側の制限に注意
2. **IP制限** - 同一IPからの大量アクセス制限
3. **リソース制限** - ローカルマシンのリソース上限

### セキュリティ

1. **プロキシ使用** - 必要に応じてプロキシ経由
2. **ログ管理** - 機密情報をログに記録しない
3. **アクセス記録** - 実行履歴の適切な管理

## 📞 サポート

### トラブルシューティング

1. **メモリ不足** → エージェント数を減らす
2. **ネットワークエラー** → ネットワーク接続を確認
3. **クリック失敗** → 対象サイトの構造変更を確認

### パフォーマンス問題

1. **速度が遅い** → エージェント数を増やす
2. **エラーが多い** → クリック間隔を延長
3. **メモリリーク** → バッチサイズを小さくする

問題が発生した場合は以下の情報と共に報告：
- OS・Pythonバージョン
- エラーメッセージ
- multi_agent_clicker.log の内容
- システムリソース使用状況