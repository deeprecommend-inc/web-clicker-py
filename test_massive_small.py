#!/usr/bin/env python3
"""
大規模クリッカーの小規模テスト (1000クリック)
"""

from massive_ad_clicker import MassiveAdClicker
import json
from datetime import datetime

def main():
    print("🧪 大規模クリッカー小規模テスト (1000クリック)")
    print("=" * 60)
    
    # 小規模設定
    clicker = MassiveAdClicker(
        target_clicks=1000,      # 1000クリックでテスト
        max_workers=4,           # 4ワーカー
        use_multiprocessing=True,
        clicks_per_session=250   # セッションあたり250クリック
    )
    
    try:
        results = clicker.run_massive_clicking()
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f'small_test_results_{timestamp}.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 結果ファイル: {results_file}")
        
        # パフォーマンス評価
        clicks_per_sec = results.get('clicks_per_second', 0)
        estimated_time_for_100k = 100000 / clicks_per_sec if clicks_per_sec > 0 else float('inf')
        
        print()
        print(f"🚀 パフォーマンス評価:")
        print(f"   小規模テスト速度: {clicks_per_sec:.1f} clicks/sec")
        print(f"   10万クリック予想時間: {estimated_time_for_100k/60:.1f} 分")
        
        if clicks_per_sec > 100:
            print("✅ 高性能! 10万クリック実行に適しています")
        elif clicks_per_sec > 50:
            print("⚠️ 中程度の性能。実行は可能ですが時間がかかります")
        else:
            print("❌ 性能が低いです。設定調整が必要かもしれません")
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")

if __name__ == "__main__":
    main()