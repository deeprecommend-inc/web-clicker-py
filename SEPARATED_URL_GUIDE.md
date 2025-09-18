# 分離型URL広告クリックシステム

## 🎯 概要

**site_url**（アクセス対象サイト）と**ad_url**（クリック対象広告）を明確に分離したシステム

## 📋 URL分離の利点

### 従来型 vs 分離型

| 項目 | 従来型 | 分離型 |
|------|--------|--------|
| **URL管理** | サイト内の広告を自動検出 | site_url と ad_url を明確に分離 |
| **精度** | 広告検出に依存 | 指定URLに確実アクセス |
| **カスタマイズ** | 限定的 | 完全にカスタマイズ可能 |
| **効果測定** | 不正確 | 正確な広告効果測定 |
| **制御** | 自動 | 完全制御 |

## 🚀 基本的な使用方法

### 1. デフォルト設定での実行

```bash
python3 separated_url_clicker.py
```

### 2. カスタムURL設定

```python
from separated_url_clicker import SeparatedUrlController

# カスタムURL設定
site_urls = [
    "https://kimagureokazu.com/stripchat-free-50coin-japan/",
    "https://example-blog.com/ad-page/",
    "https://affiliate-site.com/landing/"
]

ad_urls = [
    "https://stripchat.com/signup?utm_source=kimagure&utm_campaign=test",
    "https://target-ad-site.com/click?ref=12345",
    "https://affiliate-network.com/click/abcdef"
]

# 実行
controller = SeparatedUrlController(total_target=5000, max_agents=10)
results = controller.run_separated_campaign(
    site_urls=site_urls,
    ad_urls=ad_urls
)
```

## ⚙️ URL設定詳細

### site_url（アクセス対象サイト）

```python
site_urls = [
    # 広告を表示するページ
    "https://kimagureokazu.com/stripchat-free-50coin-japan/",
    
    # ブログ記事ページ
    "https://example-blog.com/review-article/",
    
    # ランディングページ
    "https://landing-page.com/offer/",
    
    # その他のコンテンツページ
    "https://content-site.com/article-123/"
]
```

**役割:**
- 広告を表示させるためのページアクセス
- 自然な流入を模倣
- 複数のページをローテーション
- 広告表示の前提条件を満たす

### ad_url（クリック対象広告）

```python
ad_urls = [
    # メインターゲット広告
    "https://stripchat.com/signup?utm_source=kimagure&utm_medium=blog&utm_campaign=free50coin",
    
    # サブターゲット広告
    "https://jp.stripchat.com/girls?ref=affiliate123",
    
    # 別のアフィリエイト先
    "https://chaturbate.com/affiliates/in/?tour=07Yh&campaign=abc&room=",
    
    # 直接課金ページ
    "https://target-service.com/signup?aff_id=12345"
]
```

**役割:**
- 実際の収益発生ポイント
- 明確なアフィリエイトトラッキング
- UTMパラメータでの効果測定
- 確実な広告クリック

## 🔧 クリック方法の選択

### 1. new_tab（推奨）

```python
# 新しいタブで広告を開く
click_method = 'new_tab'

# 動作:
# 1. site_urlにアクセス
# 2. 新しいタブでad_urlを開く
# 3. 2-4秒滞在
# 4. タブを閉じて元のページに戻る
```

### 2. javascript（高速）

```python
# JavaScriptで広告URLにアクセス
click_method = 'javascript'

# 動作:
# 1. site_urlにアクセス
# 2. バックグラウンドでad_urlにリクエスト送信
# 3. ページ遷移なし
```

### 3. same_tab（自然）

```python
# 同じタブで広告ページに移動
click_method = 'same_tab'

# 動作:
# 1. site_urlにアクセス
# 2. ad_urlに直接移動
# 3. 2-4秒滞在
# 4. ブラウザバックで元のページに戻る
```

## 📊 実行例とログ

### コンソール出力例

```
🎯 分離型広告クリックシステム
==================================================
site_url: アクセス対象サイト
ad_url: クリック対象広告

目標: 10,000クリック
最大エージェント数: 15

📋 URL設定:
【アクセス対象サイト】
  1. https://kimagureokazu.com/stripchat-free-50coin-japan/
  2. https://example-blog.com/article/

【クリック対象広告】
  1. https://stripchat.com/signup?utm_source=kimagure&utm_campaign=test
  2. https://jp.stripchat.com/girls?ref=affiliate123

================================================================================
分離型広告クリックキャンペーン開始
目標総クリック数: 10,000
最大同時エージェント数: 15
対象サイト数: 2
広告URL数: 2
================================================================================

2025-09-18 10:00:00 - INFO - Agent 0: サイトアクセス -> https://kimagureokazu.com/...
2025-09-18 10:00:03 - INFO - Agent 0: サイトアクセス成功
2025-09-18 10:00:05 - INFO - Agent 0: 広告URLクリック実行 -> https://stripchat.com/signup...
2025-09-18 10:00:08 - INFO - Agent 0: 広告クリック成功 -> https://stripchat.com/signup...
2025-09-18 10:00:08 - INFO - Agent 0: 進捗 1/666
```

### JSON結果例

```json
{
  "campaign_summary": {
    "type": "separated_url_campaign",
    "target_clicks": 10000,
    "actual_clicks": 9850,
    "success_rate": 98.5,
    "total_agents": 15,
    "duration_minutes": 25.5,
    "clicks_per_second": 6.43
  },
  "url_configuration": {
    "site_urls": [
      "https://kimagureokazu.com/stripchat-free-50coin-japan/"
    ],
    "ad_urls": [
      "https://stripchat.com/signup?utm_source=kimagure&utm_campaign=test"
    ]
  },
  "agent_results": [
    {
      "agent_id": 0,
      "successful_clicks": 650,
      "clicked_ads": [
        {
          "url": "https://stripchat.com/signup?utm_source=kimagure&utm_campaign=test",
          "method": "new_tab",
          "timestamp": "2025-09-18T10:00:08.123456"
        }
      ]
    }
  ]
}
```

## 🎛️ 高度なカスタマイズ

### 1. 動的URL生成

```python
import datetime

def generate_dynamic_ads():
    """動的に広告URLを生成"""
    base_url = "https://stripchat.com/signup"
    
    # 現在時刻をキャンペーンIDに使用
    campaign_id = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    
    return [
        f"{base_url}?utm_source=kimagure&utm_campaign={campaign_id}_main",
        f"{base_url}?utm_source=kimagure&utm_campaign={campaign_id}_sub",
    ]

# 使用例
dynamic_ads = generate_dynamic_ads()
controller.run_separated_campaign(ad_urls=dynamic_ads)
```

### 2. A/Bテスト実装

```python
def ab_test_campaign():
    """A/Bテスト用の並列実行"""
    
    # パターンA
    pattern_a_ads = [
        "https://stripchat.com/signup?utm_campaign=pattern_a&utm_content=button"
    ]
    
    # パターンB
    pattern_b_ads = [
        "https://stripchat.com/signup?utm_campaign=pattern_b&utm_content=banner"
    ]
    
    # 並列実行
    controller_a = SeparatedUrlController(total_target=5000)
    controller_b = SeparatedUrlController(total_target=5000)
    
    results_a = controller_a.run_separated_campaign(ad_urls=pattern_a_ads)
    results_b = controller_b.run_separated_campaign(ad_urls=pattern_b_ads)
    
    return results_a, results_b
```

### 3. 時間帯別実行

```python
import schedule
import time

def scheduled_campaign():
    """時間帯別の自動実行"""
    
    # 朝の実行（軽負荷）
    schedule.every().day.at("09:00").do(
        lambda: controller.run_separated_campaign(
            ad_urls=morning_ads, 
            total_target=1000
        )
    )
    
    # 昼の実行（中負荷）
    schedule.every().day.at("12:00").do(
        lambda: controller.run_separated_campaign(
            ad_urls=afternoon_ads, 
            total_target=3000
        )
    )
    
    # 夜の実行（高負荷）
    schedule.every().day.at("20:00").do(
        lambda: controller.run_separated_campaign(
            ad_urls=evening_ads, 
            total_target=6000
        )
    )
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

## 🔍 トラッキングとAnalytics

### UTMパラメータの活用

```python
def create_tracked_urls(base_url: str, campaign_name: str) -> List[str]:
    """トラッキング用URLを生成"""
    
    variations = [
        {
            'utm_medium': 'blog',
            'utm_content': 'button',
            'utm_term': 'signup'
        },
        {
            'utm_medium': 'banner',
            'utm_content': 'image',
            'utm_term': 'register'
        }
    ]
    
    tracked_urls = []
    for i, variation in enumerate(variations):
        params = {
            'utm_source': 'kimagure_automation',
            'utm_campaign': f'{campaign_name}_{i+1}',
            **variation
        }
        
        param_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        tracked_url = f'{base_url}?{param_string}'
        tracked_urls.append(tracked_url)
    
    return tracked_urls

# 使用例
tracked_ads = create_tracked_urls(
    base_url="https://stripchat.com/signup",
    campaign_name="automated_test"
)
```

### 効果測定レポート

```python
def generate_analytics_report(results):
    """詳細な効果測定レポート"""
    
    # URL別の成功率
    url_stats = {}
    for result in results:
        for click in result.get('clicked_ads', []):
            url = click['url']
            if url not in url_stats:
                url_stats[url] = {'clicks': 0, 'methods': {}}
            
            url_stats[url]['clicks'] += 1
            method = click['method']
            url_stats[url]['methods'][method] = url_stats[url]['methods'].get(method, 0) + 1
    
    print("📊 URL別効果測定:")
    for url, stats in url_stats.items():
        print(f"URL: {url}")
        print(f"  総クリック: {stats['clicks']}")
        print(f"  方法別: {stats['methods']}")
        print()
```

## ⚠️ 注意事項

### 1. URLの正確性

```python
# 正しいURL形式
✅ "https://stripchat.com/signup?utm_source=test"
❌ "stripchat.com/signup"  # httpスキーマ必須
❌ "https://stripchat.com/signup?param"  # パラメータに値が必要
```

### 2. アフィリエイトリンクの有効性

```python
# アフィリエイトIDの確認
def validate_affiliate_url(url: str) -> bool:
    """アフィリエイトURLの有効性チェック"""
    required_params = ['utm_source', 'aff_id', 'ref']
    
    for param in required_params:
        if param in url:
            return True
    
    return False
```

### 3. レート制限の考慮

```python
# 適切な間隔設定
delay_range = (3, 8)  # 3-8秒間隔（推奨）
delay_range = (1, 3)  # 1-3秒間隔（高速、リスク高）
delay_range = (5, 15) # 5-15秒間隔（安全、低速）
```

## 📈 パフォーマンス最適化

### 最適なURL数

```python
# 推奨設定
site_urls = 2-5個   # 多すぎると分散しすぎる
ad_urls = 3-10個    # A/Bテスト可能な範囲

# NGパターン
site_urls = 20個+   # 効果が薄い
ad_urls = 1個       # 単一点障害リスク
```

### バッチサイズ調整

```python
# システムリソースに応じて調整
max_agents = 5     # 低スペック環境
max_agents = 15    # 推奨設定
max_agents = 30    # 高スペック環境
```

分離型システムにより、site_urlとad_urlを明確に管理し、より精密で効果的な広告クリック自動化が実現できます。