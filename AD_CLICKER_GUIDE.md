# 広告自動クリックスクリプト 使用ガイド

## 📋 概要

指定されたWebサイト（https://kimagureokazu.com/stripchat-free-50coin-japan/）の広告リンク（aタグ）を自動でクリックするスクリプトです。

## 🚀 実行方法

### 基本実行

```bash
python3 ad_clicker.py
```

### カスタム設定での実行

```python
from ad_clicker import AdClicker

# カスタム設定
clicker = AdClicker(
    headless=True,           # ヘッドレスモード
    delay_range=(2, 6)       # クリック間隔2-6秒
)

# 実行
results = clicker.run_ad_clicking(
    target_url="https://kimagureokazu.com/stripchat-free-50coin-japan/",
    max_clicks=20,           # 最大20クリック
    session_duration=900     # 15分間実行
)
```

## ⚙️ 設定オプション

### AdClickerクラスのパラメータ

- `headless`: ブラウザ表示の有無（True=非表示, False=表示）
- `delay_range`: クリック間隔のランダム範囲（秒）

### run_ad_clickingメソッドのパラメータ

- `target_url`: 対象URL
- `max_clicks`: 最大クリック数（デフォルト: 10）
- `session_duration`: セッション時間（秒、デフォルト: 300）

## 🎯 検出される広告リンクの種類

スクリプトは以下の種類の広告リンクを自動検出します：

1. **アフィリエイトサイト関連**
   - Stripchat関連リンク
   - Chaturbate関連リンク
   - その他カメラサイト

2. **リンクパターン**
   - `href*="affiliate"` - アフィリエイトリンク
   - `href*="ref="` - リファラルリンク
   - `href*="utm_"` - UTMパラメータ付き
   - `target="_blank"` - 新タブで開くリンク

3. **CSSクラス・要素**
   - `.ad-link` - 広告リンククラス
   - `.affiliate-link` - アフィリエイトリンククラス
   - `.banner-link` - バナーリンククラス
   - `div.advertisement a` - 広告エリア内のリンク

## 📊 実行結果

### コンソール出力例

```
================================================================================
広告自動クリックスクリプト
================================================================================
対象URL: https://kimagureokazu.com/stripchat-free-50coin-japan/

2025-09-17 17:30:00,000 - INFO - 広告クリックセッション開始
2025-09-17 17:30:00,000 - INFO - 最大クリック数: 15, セッション時間: 600秒
2025-09-17 17:30:03,000 - INFO - 検出された広告リンク数: 8
2025-09-17 17:30:05,000 - INFO - クリック実行: Stripchatバナー -> https://stripchat.com/...
2025-09-17 17:30:05,500 - INFO - クリック成功: Stripchatバナー
2025-09-17 17:30:08,000 - INFO - 待機: 5.23秒
...
============================================================
広告クリックセッション完了
総クリック数: 15
成功クリック数: 14
成功率: 93.3%
実行時間: 287.5秒
============================================================

📊 クリック結果:
   成功: 14/15
   成功率: 93.3%
   実行時間: 287.5秒

📁 詳細結果: ad_click_results.json
📝 実行ログ: ad_clicker.log
```

### 出力ファイル

1. **ad_click_results.json** - 詳細なクリック結果
```json
{
  "start_time": "2025-09-17T17:30:00.000000",
  "target_url": "https://kimagureokazu.com/stripchat-free-50coin-japan/",
  "clicked_links": [
    {
      "href": "https://stripchat.com/...",
      "text": "Stripchatバナー",
      "type": "image",
      "timestamp": "2025-09-17T17:30:05.500000"
    }
  ],
  "total_clicks": 15,
  "successful_clicks": 14,
  "success_rate": 93.3,
  "duration": 287.5
}
```

2. **ad_clicker.log** - 詳細な実行ログ

## 🛡️ 安全機能

### ボット検出回避

- ランダムなクリック間隔（3-8秒）
- 自然なマウス動作シミュレーション
- User-Agentのランダム化
- スクロール動作の自然化

### エラーハンドリング

- 要素が見つからない場合の自動リトライ
- ページ読み込み失敗時の再試行
- ネットワークエラーの処理
- 予期しないポップアップの処理

### 重複防止

- 同一セッション内での重複クリック防止
- クリック済みリンクの記録と管理

## 🔧 トラブルシューティング

### よくある問題

1. **広告が検出されない**
```bash
# 解決方法: headlessモードを無効にしてブラウザを確認
clicker = AdClicker(headless=False)
```

2. **クリックが失敗する**
```python
# より長い待機時間を設定
clicker = AdClicker(delay_range=(5, 10))
```

3. **ページが読み込まれない**
```python
# より長いセッション時間を設定
results = clicker.run_ad_clicking(session_duration=1200)  # 20分
```

## ⚡ パフォーマンス最適化

### 高速化設定

```python
# ヘッドレスモードで高速化
clicker = AdClicker(
    headless=True,
    delay_range=(1, 3)  # 短い間隔
)
```

### 安定性重視設定

```python
# 安定性を重視した設定
clicker = AdClicker(
    headless=False,
    delay_range=(5, 10)  # 長い間隔
)
```

## 📈 使用例

### 短時間テスト

```python
# 5分間で最大5クリックのテスト
results = clicker.run_ad_clicking(
    target_url="https://kimagureokazu.com/stripchat-free-50coin-japan/",
    max_clicks=5,
    session_duration=300
)
```

### 長時間運用

```python
# 30分間で最大50クリック
results = clicker.run_ad_clicking(
    target_url="https://kimagureokazu.com/stripchat-free-50coin-japan/",
    max_clicks=50,
    session_duration=1800
)
```

### 複数セッション実行

```python
import time

clicker = AdClicker(headless=True)

for session in range(3):
    print(f"セッション {session + 1} 開始")
    results = clicker.run_ad_clicking(
        target_url="https://kimagureokazu.com/stripchat-free-50coin-japan/",
        max_clicks=10,
        session_duration=600
    )
    print(f"セッション {session + 1} 完了: {results['successful_clicks']}クリック")
    time.sleep(300)  # セッション間の休憩
```

## ⚠️ 注意事項

1. **利用規約の確認**
   - 対象サイトの利用規約を事前に確認してください
   - 過度なアクセスはサーバーに負荷をかける可能性があります

2. **レート制限**
   - 適切なクリック間隔を設定してください
   - 短時間での大量クリックは避けてください

3. **法的責任**
   - スクリプトの使用は自己責任で行ってください
   - 不正な利用は禁止されています

## 🛠️ カスタマイズ

### 新しい広告パターンの追加

```python
# ad_clicker.py の find_ad_links メソッド内で追加
ad_selectors = [
    'a[href*="your-new-pattern"]',  # 新しいパターンを追加
    # 既存のパターン...
]
```

### カスタムフィルタリング

```python
def custom_link_filter(link_info):
    """カスタムリンクフィルタ"""
    href = link_info['href']
    # 特定のドメインのみをクリック
    return 'target-domain.com' in href

# フィルタを適用
filtered_links = [link for link in ad_links if custom_link_filter(link)]
```

## 📞 サポート

問題が発生した場合は、以下の情報を含めて報告してください：

- 実行環境（OS, Python バージョン）
- エラーメッセージ
- ad_clicker.log の内容
- 実行時の設定