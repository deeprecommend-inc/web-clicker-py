#!/usr/bin/env python3
"""
最適化クリッカーの小規模テスト (1000クリック)
"""

from optimized_massive_clicker import OptimizedMassiveClicker
import json
from datetime import datetime

def main():
    print("🧪 最適化クリッカー小規模テスト (1000クリック)")
    print("=" * 60)
    
    # 小規模設定
    clicker = OptimizedMassiveClicker(
        target_clicks=1000,      # 1000クリックでテスト
        max_workers=4,           # 4ワーカー
        clicks_per_worker=250    # ワーカーあたり250クリック
    )
    
    try:
        results = clicker.run_massive_clicking()
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f'optimized_small_test_{timestamp}.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 結果ファイル: {results_file}")
        
        # パフォーマンス評価
        clicks_per_sec = results.get('clicks_per_second', 0)
        success_rate = results.get('success_rate', 0)
        duration = results.get('total_duration', 0)
        
        print()
        print(f"🚀 パフォーマンス評価:")
        print(f"   実行時間: {duration:.1f}秒")
        print(f"   成功クリック: {results.get('successful_clicks', 0):,}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   速度: {clicks_per_sec:.1f} clicks/sec")
        
        if clicks_per_sec > 0:
            estimated_time_for_100k = 100000 / clicks_per_sec
            print(f"   10万クリック予想時間: {estimated_time_for_100k/60:.1f} 分")
        
        if clicks_per_sec > 200:
            print("✅ 超高性能! 10万クリック実行に最適です")
        elif clicks_per_sec > 100:
            print("✅ 高性能! 10万クリック実行に適しています")
        elif clicks_per_sec > 50:
            print("⚠️ 中程度の性能。実行は可能ですが時間がかかります")
        else:
            print("❌ 性能が低いです。設定調整が必要かもしれません")
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")

if __name__ == "__main__":
    main()