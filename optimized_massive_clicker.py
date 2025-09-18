#!/usr/bin/env python3
"""
最適化された大規模広告クリックスクリプト - 10万回クリック対応
スレッドベース、メモリ最適化、高性能実装
"""

import time
import logging
import random
import threading
import queue
import json
import gc
import psutil
import os
import signal
import sys
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementClickInterceptedException,
    WebDriverException
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ロギング設定（スレッドセーフ）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[
        logging.FileHandler('optimized_massive_click.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ClickResult:
    """クリック結果データクラス"""
    worker_id: int
    click_count: int
    success_count: int
    fail_count: int
    start_time: str
    end_time: str
    duration: float
    ads_detected: int
    error_messages: List[str]

class OptimizedMassiveClicker:
    """最適化された大規模広告クリックエンジン"""
    
    def __init__(self, 
                 target_clicks: int = 100000,
                 max_workers: int = None,
                 clicks_per_worker: int = 2000):
        """
        初期化
        
        Args:
            target_clicks: 目標クリック数
            max_workers: 最大ワーカー数（Noneで自動設定）
            clicks_per_worker: ワーカーあたりのクリック数
        """
        self.target_clicks = target_clicks
        self.clicks_per_worker = clicks_per_worker
        
        # システムリソース最適化
        cpu_count = os.cpu_count() or 4
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if max_workers is None:
            # CPU・メモリに基づく最適ワーカー数計算
            self.max_workers = min(cpu_count * 3, int(memory_gb / 2), 32)
        else:
            self.max_workers = max_workers
        
        # 統計管理
        self.total_clicks = 0
        self.total_success = 0
        self.total_failures = 0
        self.worker_results = []
        self.start_time = None
        self.stop_event = threading.Event()
        self.stats_lock = threading.Lock()
        
        # 結果キュー（スレッドセーフ）
        self.result_queue = queue.Queue()
        
        logger.info(f"🚀 OptimizedMassiveClicker初期化完了")
        logger.info(f"   目標クリック数: {target_clicks:,}")
        logger.info(f"   最大ワーカー数: {self.max_workers}")
        logger.info(f"   CPU数: {cpu_count}, メモリ: {memory_gb:.1f}GB")
    
    def create_ultra_fast_driver(self) -> webdriver.Chrome:
        """超高速WebDriverを作成"""
        options = Options()
        
        # 最大パフォーマンス設定
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        options.add_argument('--disable-css')
        options.add_argument('--window-size=400,300')  # 極小ウィンドウ
        options.add_argument('--disable-logging')
        options.add_argument('--silent')
        
        # SSL/証明書エラーの無視
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--allow-running-insecure-content')
        
        # メモリ使用量削減
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=256')
        
        # WebDriver初期化
        try:
            driver_path = ChromeDriverManager().install()
            
            # ChromeDriverの実際のパスを特定
            if 'chromedriver-linux64' in driver_path:
                driver_dir = os.path.dirname(driver_path)
                actual_driver = os.path.join(driver_dir, 'chromedriver-linux64', 'chromedriver')
            else:
                driver_dir = os.path.dirname(driver_path) 
                actual_driver = os.path.join(driver_dir, 'chromedriver')
                
            if not os.path.exists(actual_driver):
                for root, dirs, files in os.walk(os.path.dirname(driver_path)):
                    for file in files:
                        if file == 'chromedriver':
                            actual_driver = os.path.join(root, file)
                            break
                    if os.path.exists(actual_driver):
                        break
            
            os.chmod(actual_driver, 0o755)
            
            service = Service(actual_driver)
            driver = webdriver.Chrome(service=service, options=options)
            
            # タイムアウト設定
            driver.set_page_load_timeout(5)
            driver.implicitly_wait(0.5)
            
            return driver
            
        except Exception as e:
            logger.error(f"WebDriver作成エラー: {e}")
            raise
    
    def create_minimal_test_page(self) -> str:
        """最小限のテストページ作成"""
        # 200個の広告要素を含む超軽量HTML
        ads_html = "\n".join([
            f'<div class="ad" id="ad{i}" onclick="console.log(\'click{i}\')" '
            f'style="width:10px;height:10px;background:#f00;display:inline-block;">A{i%10}</div>'
            for i in range(200)
        ])
        
        html_content = f"""<!DOCTYPE html>
<html><head><title>Ultra Fast Test</title></head><body>
<div id="ads">{ads_html}</div>
</body></html>"""
        
        # ユニークなファイル名でスレッド間の競合を避ける
        test_file_path = f'/tmp/ultra_test_{os.getpid()}_{threading.get_ident()}_{int(time.time()*1000)}.html'
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return f'file://{test_file_path}'
    
    def worker_ultra_fast_clicking(self, worker_id: int, target_clicks: int) -> ClickResult:
        """超高速クリックワーカー"""
        start_time = datetime.now()
        success_count = 0
        fail_count = 0
        ads_detected = 0
        error_messages = []
        driver = None
        test_file = None
        
        try:
            logger.info(f"⚡ Worker-{worker_id}: 超高速セッション開始 (目標: {target_clicks}クリック)")
            
            # WebDriver作成
            driver = self.create_ultra_fast_driver()
            
            # テストページ読み込み
            test_url = self.create_minimal_test_page()
            test_file = test_url.replace('file://', '')
            driver.get(test_url)
            
            # 広告要素検出
            ad_elements = driver.find_elements(By.CSS_SELECTOR, '.ad')
            ads_detected = len(ad_elements)
            
            if not ad_elements:
                error_messages.append("広告要素が見つかりません")
                return ClickResult(
                    worker_id=worker_id,
                    click_count=0,
                    success_count=0,
                    fail_count=1,
                    start_time=start_time.isoformat(),
                    end_time=datetime.now().isoformat(),
                    duration=0,
                    ads_detected=0,
                    error_messages=error_messages
                )
            
            # 超高速クリックループ
            click_count = 0
            session_start = time.time()
            
            # 広告要素リストをキャッシュ
            ad_cache = ad_elements.copy()
            cache_size = len(ad_cache)
            
            while click_count < target_clicks and not self.stop_event.is_set():
                try:
                    # ランダムな広告要素をインデックスで選択
                    ad_index = random.randint(0, cache_size - 1)
                    ad_element = ad_cache[ad_index]
                    
                    # JavaScriptで超高速クリック（DOM操作なし）
                    driver.execute_script("arguments[0].click();", ad_element)
                    
                    success_count += 1
                    click_count += 1
                    
                    # 大量クリック時のガベージコレクション
                    if click_count % 500 == 0:
                        gc.collect()
                        
                        # 進捗報告
                        elapsed = time.time() - session_start
                        rate = click_count / elapsed if elapsed > 0 else 0
                        logger.info(f"⚡ Worker-{worker_id}: {click_count}/{target_clicks} "
                                  f"({rate:.0f} clicks/sec)")
                        
                        # 統計更新
                        with self.stats_lock:
                            self.total_success += 500
                    
                    # 超高速実行のため待機なし
                    
                except Exception as e:
                    fail_count += 1
                    if len(error_messages) < 5:  # エラーメッセージ制限
                        error_messages.append(str(e))
                    
                    # 大量連続エラーでセッション終了
                    if fail_count > 200:
                        logger.warning(f"⚠️ Worker-{worker_id}: 大量エラー発生")
                        break
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            rate = success_count / duration if duration > 0 else 0
            
            logger.info(f"✅ Worker-{worker_id}: 超高速セッション完了 "
                       f"({success_count:,}成功, {rate:.0f} clicks/sec)")
            
            return ClickResult(
                worker_id=worker_id,
                click_count=click_count,
                success_count=success_count,
                fail_count=fail_count,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=duration,
                ads_detected=ads_detected,
                error_messages=error_messages
            )
            
        except Exception as e:
            error_msg = f"Worker-{worker_id} 致命的エラー: {e}"
            logger.error(error_msg)
            error_messages.append(error_msg)
            
            return ClickResult(
                worker_id=worker_id,
                click_count=0,
                success_count=0,
                fail_count=1,
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                duration=0,
                ads_detected=0,
                error_messages=error_messages
            )
            
        finally:
            # クリーンアップ
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            # 一時ファイル削除
            if test_file and os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass
    
    def monitor_progress(self):
        """進捗監視スレッド"""
        last_total = 0
        start_time = time.time()
        
        while not self.stop_event.is_set():
            try:
                with self.stats_lock:
                    current_total = self.total_success
                
                elapsed = time.time() - start_time
                
                if elapsed > 5:  # 5秒後から進捗表示
                    overall_rate = current_total / elapsed
                    recent_rate = (current_total - last_total) / 5  # 5秒間の平均
                    
                    progress = (current_total / self.target_clicks) * 100
                    
                    if overall_rate > 0:
                        remaining_time = (self.target_clicks - current_total) / overall_rate
                        logger.info(f"🎯 進捗: {current_total:,}/{self.target_clicks:,} "
                                   f"({progress:.1f}%) | "
                                   f"速度: {overall_rate:.0f}/sec | "
                                   f"残り: {remaining_time/60:.1f}分")
                    
                    # CPU・メモリ監視
                    cpu_percent = psutil.cpu_percent()
                    memory_percent = psutil.virtual_memory().percent
                    logger.info(f"📊 システム: CPU {cpu_percent:.1f}%, メモリ {memory_percent:.1f}%")
                
                last_total = current_total
                
                # 目標達成チェック
                if current_total >= self.target_clicks:
                    logger.info(f"🎉 目標達成! {current_total:,}クリック完了")
                    self.stop_event.set()
                    break
                
            except Exception as e:
                logger.debug(f"進捗監視エラー: {e}")
            
            time.sleep(5)
    
    def run_massive_clicking(self) -> Dict:
        """大規模クリック実行"""
        self.start_time = datetime.now()
        logger.info(f"🚀 超大規模クリック開始: 目標 {self.target_clicks:,} クリック")
        
        # 進捗監視スレッド開始
        progress_thread = threading.Thread(target=self.monitor_progress, daemon=True)
        progress_thread.start()
        
        try:
            # ワーカー数計算
            workers_needed = min(
                (self.target_clicks + self.clicks_per_worker - 1) // self.clicks_per_worker,
                self.max_workers
            )
            
            logger.info(f"🧵 スレッド実行: {workers_needed} ワーカー開始")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                clicks_assigned = 0
                for worker_id in range(workers_needed):
                    if self.stop_event.is_set():
                        break
                    
                    remaining_clicks = self.target_clicks - clicks_assigned
                    worker_clicks = min(self.clicks_per_worker, remaining_clicks)
                    
                    if worker_clicks <= 0:
                        break
                    
                    future = executor.submit(
                        self.worker_ultra_fast_clicking, 
                        worker_id, 
                        worker_clicks
                    )
                    futures.append(future)
                    clicks_assigned += worker_clicks
                
                # 結果収集
                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        break
                    try:
                        result = future.result(timeout=600)  # 10分タイムアウト
                        self.worker_results.append(result)
                        
                        with self.stats_lock:
                            self.total_clicks += result.click_count
                            # total_successは各ワーカーで更新済み
                            self.total_failures += result.fail_count
                        
                    except Exception as e:
                        logger.error(f"ワーカー結果取得エラー: {e}")
            
        except KeyboardInterrupt:
            logger.info("🛑 ユーザーによる中断")
            self.stop_event.set()
        except Exception as e:
            logger.error(f"❌ 実行エラー: {e}")
            self.stop_event.set()
        
        # 終了処理
        self.stop_event.set()
        time.sleep(1)  # スレッド終了待機
        
        # 最終統計計算
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # ワーカー結果から正確な成功数を再計算
        actual_success = sum(r.success_count for r in self.worker_results)
        actual_failures = sum(r.fail_count for r in self.worker_results)
        actual_total = actual_success + actual_failures
        
        results = {
            'target_clicks': self.target_clicks,
            'total_clicks': actual_total,
            'successful_clicks': actual_success,
            'failed_clicks': actual_failures,
            'success_rate': (actual_success / actual_total * 100) if actual_total > 0 else 0,
            'total_duration': total_duration,
            'clicks_per_second': actual_success / total_duration if total_duration > 0 else 0,
            'workers_used': len(self.worker_results),
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'worker_results': [asdict(r) for r in self.worker_results]
        }
        
        # 結果表示
        logger.info("="*80)
        logger.info("🎯 超大規模クリック完了")
        logger.info(f"📊 目標クリック数: {self.target_clicks:,}")
        logger.info(f"✅ 成功クリック数: {actual_success:,}")
        logger.info(f"❌ 失敗クリック数: {actual_failures:,}")
        logger.info(f"📈 成功率: {results['success_rate']:.1f}%")
        logger.info(f"⚡ 平均速度: {results['clicks_per_second']:.0f} clicks/sec")
        logger.info(f"⏱️ 実行時間: {total_duration:.1f}秒")
        logger.info(f"👥 使用ワーカー数: {len(self.worker_results)}")
        logger.info("="*80)
        
        return results

def main():
    """メイン実行関数"""
    print("⚡ 超大規模広告クリックシステム")
    print("=" * 80)
    print()
    
    # 設定
    target_clicks = 100000  # 10万クリック
    max_workers = 16        # 最大16ワーカー
    clicks_per_worker = 8000  # ワーカーあたり8000クリック
    
    print(f"🎯 目標クリック数: {target_clicks:,}")
    print(f"💻 システム情報:")
    print(f"   CPU: {os.cpu_count()} コア")
    print(f"   メモリ: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print(f"   最大ワーカー数: {max_workers}")
    print()
    
    # 実行確認
    response = input("超大規模クリック (10万回) を実行しますか？ (y/N): ").strip().lower()
    if response != 'y':
        print("❌ 実行をキャンセルしました")
        return
    
    try:
        # クリッカー初期化
        clicker = OptimizedMassiveClicker(
            target_clicks=target_clicks,
            max_workers=max_workers,
            clicks_per_worker=clicks_per_worker
        )
        
        # 実行
        results = clicker.run_massive_clicking()
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f'optimized_massive_results_{timestamp}.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"📁 詳細結果: {results_file}")
        print(f"📝 実行ログ: optimized_massive_click.log")
        
    except Exception as e:
        logger.error(f"❌ 致命的エラー: {e}")
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()