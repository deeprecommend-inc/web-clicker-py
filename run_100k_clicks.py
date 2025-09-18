#!/usr/bin/env python3
"""
10万クリック直接実行スクリプト
"""

from ultra_massive_clicker import UltraMassiveClicker
import json
from datetime import datetime
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("⚡ 10万クリック実行開始")
    print("=" * 60)
    
    try:
        # 10万クリック実行
        clicker = UltraMassiveClicker(target_clicks=100000)
        logger.info("🚀 10万クリック開始")
        
        results = clicker.run_ultra_massive_clicking()
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f'100k_clicks_results_{timestamp}.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 結果表示
        print()
        print("🎉 10万クリック完了!")
        print(f"   成功クリック: {results['successful_clicks']:,}")
        print(f"   成功率: {results['success_rate']:.1f}%")
        print(f"   実行時間: {results['total_duration']:.1f}秒 ({results['total_duration']/60:.1f}分)")
        print(f"   平均速度: {results['clicks_per_second']:.0f} clicks/sec")
        print(f"   使用ワーカー: {results['workers_used']}")
        print(f"   結果ファイル: {results_file}")
        
        # パフォーマンス評価
        if results['clicks_per_second'] > 500:
            print("🚀 超高性能!")
        elif results['clicks_per_second'] > 200:
            print("⚡ 高性能!")
        elif results['clicks_per_second'] > 100:
            print("✅ 良好な性能")
        else:
            print("⚠️ 標準的な性能")
            
    except KeyboardInterrupt:
        print("\n🛑 ユーザーによる中断")
    except Exception as e:
        print(f"❌ エラー: {e}")
        logger.error(f"実行エラー: {e}")

if __name__ == "__main__":
    main()