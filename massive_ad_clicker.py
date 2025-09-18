#!/usr/bin/env python3
"""
大規模広告クリックスクリプト - 10万回クリック対応
マルチスレッド、メモリ最適化、高性能実装
"""

import time
import logging
import random
import threading
import multiprocessing
import queue
import json
import gc
import psutil
import os
import signal
import sys
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
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
        logging.FileHandler('massive_ad_click.log'),
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

@dataclass
class SystemStats:
    """システム統計データクラス"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    active_threads: int
    active_processes: int
    timestamp: str

class MassiveAdClicker:
    """大規模広告クリックエンジン"""
    
    def __init__(self, 
                 target_clicks: int = 100000,
                 max_workers: int = None,
                 use_multiprocessing: bool = True,
                 clicks_per_session: int = 1000,
                 session_timeout: int = 300):
        """
        初期化
        
        Args:
            target_clicks: 目標クリック数
            max_workers: 最大ワーカー数（Noneで自動設定）
            use_multiprocessing: マルチプロセシング使用
            clicks_per_session: セッションあたりのクリック数
            session_timeout: セッションタイムアウト（秒）
        """
        self.target_clicks = target_clicks
        self.clicks_per_session = clicks_per_session
        self.session_timeout = session_timeout
        self.use_multiprocessing = use_multiprocessing
        
        # システムリソース最適化
        cpu_count = multiprocessing.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if max_workers is None:
            # CPU・メモリに基づく最適ワーカー数計算
            if use_multiprocessing:
                self.max_workers = min(cpu_count * 2, int(memory_gb / 2), 32)
            else:
                self.max_workers = min(cpu_count * 4, int(memory_gb), 64)
        else:
            self.max_workers = max_workers
        
        # 統計管理
        self.total_clicks = 0
        self.total_success = 0
        self.total_failures = 0
        self.worker_results = []
        self.system_stats = []
        self.start_time = None
        self.stop_event = threading.Event()
        
        # クリック結果キュー（スレッドセーフ）
        self.result_queue = queue.Queue()
        self.stats_queue = queue.Queue()
        
        logger.info(f"🚀 MassiveAdClicker初期化完了")
        logger.info(f"   目標クリック数: {target_clicks:,}")
        logger.info(f"   最大ワーカー数: {self.max_workers}")
        logger.info(f"   マルチプロセシング: {use_multiprocessing}")
        logger.info(f"   CPU数: {cpu_count}, メモリ: {memory_gb:.1f}GB")
    
    def create_optimized_driver(self) -> webdriver.Chrome:
        """最適化されたWebDriverを作成"""
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
        options.add_argument('--single-process')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # 画像読み込み無効化
        options.add_argument('--disable-javascript')  # JavaScript無効化（クリックに支障なし）
        options.add_argument('--disable-css')  # CSS無効化
        options.add_argument('--window-size=800,600')  # 小さめウィンドウ
        
        # SSL/証明書エラーの無視
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--allow-running-insecure-content')
        
        # メモリ使用量削減
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=512')
        
        # ユーザーエージェント簡素化
        options.add_argument('--user-agent=Mozilla/5.0')
        
        # WebDriver初期化
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
        driver.set_page_load_timeout(10)
        driver.implicitly_wait(1)
        
        return driver
    
    def create_test_page_fast(self) -> str:
        """高速テストページ作成（最小限HTML）"""
        html_content = """<!DOCTYPE html>
<html><head><title>Mass Click Test</title></head><body>
<div id="ads">
""" + "\n".join([
    f'<div class="ad" onclick="console.log(\'click {i}\')" style="width:50px;height:20px;background:#ccc;margin:1px;">Ad{i}</div>'
    for i in range(100)  # 100個の広告要素
]) + """
</div></body></html>"""
        
        test_file_path = f'/tmp/mass_test_{os.getpid()}_{threading.get_ident()}.html'
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return f'file://{test_file_path}'
    
    def worker_click_session(self, worker_id: int, clicks_target: int) -> ClickResult:
        """ワーカーのクリックセッション"""
        start_time = datetime.now()
        success_count = 0
        fail_count = 0
        ads_detected = 0
        error_messages = []
        driver = None
        
        try:
            logger.info(f"🏃 Worker-{worker_id}: セッション開始 (目標: {clicks_target}クリック)")
            
            # WebDriver作成
            driver = self.create_optimized_driver()
            
            # テストページ読み込み
            test_url = self.create_test_page_fast()
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
            
            # 高速クリックループ
            click_count = 0
            session_start = time.time()
            
            while (click_count < clicks_target and 
                   not self.stop_event.is_set() and
                   time.time() - session_start < self.session_timeout):
                
                try:
                    # ランダムな広告要素をクリック
                    ad_element = random.choice(ad_elements)
                    
                    # JavaScriptで高速クリック
                    driver.execute_script("arguments[0].click();", ad_element)
                    
                    success_count += 1
                    click_count += 1
                    
                    # 100クリックごとにガベージコレクション
                    if click_count % 100 == 0:
                        gc.collect()
                        
                        # 進捗報告
                        elapsed = time.time() - session_start
                        rate = click_count / elapsed if elapsed > 0 else 0
                        logger.info(f"🎯 Worker-{worker_id}: {click_count}/{clicks_target} "
                                  f"({rate:.1f} clicks/sec)")
                    
                    # 最小待機（オプション）
                    if click_count % 50 == 0:
                        time.sleep(0.001)
                    
                except Exception as e:
                    fail_count += 1
                    if len(error_messages) < 10:  # エラーメッセージ制限
                        error_messages.append(str(e))
                    
                    # 連続エラーでセッション終了
                    if fail_count > 100:
                        logger.warning(f"⚠️ Worker-{worker_id}: 連続エラーが多すぎます")
                        break
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Worker-{worker_id}: セッション完了 "
                       f"({success_count}成功, {fail_count}失敗, {duration:.1f}秒)")
            
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
            error_msg = f"Worker-{worker_id} セッションエラー: {e}"
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
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            # 一時ファイル削除
            try:
                if 'test_url' in locals():
                    test_file = test_url.replace('file://', '')
                    if os.path.exists(test_file):
                        os.remove(test_file)
            except:
                pass
    
    def monitor_system_stats(self):
        """システム統計監視スレッド"""
        while not self.stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                stats = SystemStats(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_gb=memory.used / (1024**3),
                    active_threads=threading.active_count(),
                    active_processes=len(psutil.pids()),
                    timestamp=datetime.now().isoformat()
                )
                
                self.stats_queue.put(stats)
                
                # 5秒ごとにログ出力
                if len(self.system_stats) % 5 == 0:
                    logger.info(f"📊 システム状況: CPU {cpu_percent:.1f}%, "
                               f"メモリ {memory.percent:.1f}% ({memory.used / (1024**3):.1f}GB), "
                               f"スレッド {threading.active_count()}")
                
            except Exception as e:
                logger.debug(f"システム統計エラー: {e}")
            
            time.sleep(5)
    
    def progress_monitor(self):
        """進捗監視スレッド"""
        last_total = 0
        start_time = time.time()
        
        while not self.stop_event.is_set():
            try:
                current_total = self.total_success
                elapsed = time.time() - start_time
                
                if elapsed > 0:
                    overall_rate = current_total / elapsed
                    recent_rate = (current_total - last_total) / 10  # 10秒間の平均
                    
                    progress = (current_total / self.target_clicks) * 100
                    remaining = (self.target_clicks - current_total) / overall_rate if overall_rate > 0 else float('inf')
                    
                    logger.info(f"🎯 進捗: {current_total:,}/{self.target_clicks:,} "
                               f"({progress:.1f}%) | "
                               f"速度: {overall_rate:.1f}/sec | "
                               f"残り時間: {remaining/60:.1f}分")
                
                last_total = current_total
                
            except Exception as e:
                logger.debug(f"進捗監視エラー: {e}")
            
            time.sleep(10)
    
    def collect_results(self):
        """結果収集スレッド"""
        while not self.stop_event.is_set() or not self.result_queue.empty():
            try:
                result = self.result_queue.get(timeout=1)
                self.worker_results.append(result)
                self.total_clicks += result.click_count
                self.total_success += result.success_count
                self.total_failures += result.fail_count
                
                # 目標達成チェック
                if self.total_success >= self.target_clicks:
                    logger.info(f"🎉 目標達成! {self.total_success:,}クリック完了")
                    self.stop_event.set()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.debug(f"結果収集エラー: {e}")
    
    def run_massive_clicking(self) -> Dict:
        """大規模クリック実行"""
        self.start_time = datetime.now()
        logger.info(f"🚀 大規模クリック開始: 目標 {self.target_clicks:,} クリック")
        
        # 監視スレッド開始
        monitor_thread = threading.Thread(target=self.monitor_system_stats, daemon=True)
        progress_thread = threading.Thread(target=self.progress_monitor, daemon=True)
        collect_thread = threading.Thread(target=self.collect_results, daemon=True)
        
        monitor_thread.start()
        progress_thread.start()
        collect_thread.start()
        
        try:
            # ワーカー実行
            sessions_needed = (self.target_clicks + self.clicks_per_session - 1) // self.clicks_per_session
            
            if self.use_multiprocessing:
                self._run_with_multiprocessing(sessions_needed)
            else:
                self._run_with_threading(sessions_needed)
            
        except KeyboardInterrupt:
            logger.info("🛑 ユーザーによる中断")
            self.stop_event.set()
        except Exception as e:
            logger.error(f"❌ 実行エラー: {e}")
            self.stop_event.set()
        
        # 終了処理
        self.stop_event.set()
        time.sleep(2)  # 結果収集完了待機
        
        # 最終統計
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # システム統計収集
        while not self.stats_queue.empty():
            try:
                self.system_stats.append(self.stats_queue.get_nowait())
            except queue.Empty:
                break
        
        results = {
            'target_clicks': self.target_clicks,
            'total_clicks': self.total_clicks,
            'successful_clicks': self.total_success,
            'failed_clicks': self.total_failures,
            'success_rate': (self.total_success / self.total_clicks * 100) if self.total_clicks > 0 else 0,
            'total_duration': total_duration,
            'clicks_per_second': self.total_success / total_duration if total_duration > 0 else 0,
            'workers_used': len(self.worker_results),
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'worker_results': [asdict(r) for r in self.worker_results],
            'system_stats': [asdict(s) for s in self.system_stats]
        }
        
        # 結果表示
        logger.info("="*80)
        logger.info("🎯 大規模クリック完了")
        logger.info(f"📊 目標クリック数: {self.target_clicks:,}")
        logger.info(f"✅ 成功クリック数: {self.total_success:,}")
        logger.info(f"❌ 失敗クリック数: {self.total_failures:,}")
        logger.info(f"📈 成功率: {results['success_rate']:.1f}%")
        logger.info(f"⚡ 平均速度: {results['clicks_per_second']:.1f} clicks/sec")
        logger.info(f"⏱️ 実行時間: {total_duration:.1f}秒")
        logger.info(f"👥 使用ワーカー数: {len(self.worker_results)}")
        logger.info("="*80)
        
        return results
    
    def _run_with_threading(self, sessions_needed: int):
        """スレッド実行"""
        logger.info(f"🧵 スレッド実行: {sessions_needed} セッション, {self.max_workers} ワーカー")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i in range(sessions_needed):
                if self.stop_event.is_set():
                    break
                
                remaining_clicks = min(self.clicks_per_session, 
                                     self.target_clicks - self.total_success)
                
                if remaining_clicks <= 0:
                    break
                
                future = executor.submit(self.worker_click_session, i, remaining_clicks)
                futures.append(future)
            
            # 結果収集
            for future in as_completed(futures):
                if self.stop_event.is_set():
                    break
                try:
                    result = future.result(timeout=self.session_timeout + 60)
                    self.result_queue.put(result)
                except Exception as e:
                    logger.error(f"ワーカーエラー: {e}")
    
    def _run_with_multiprocessing(self, sessions_needed: int):
        """マルチプロセス実行"""
        logger.info(f"🔄 マルチプロセス実行: {sessions_needed} セッション, {self.max_workers} ワーカー")
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i in range(sessions_needed):
                if self.stop_event.is_set():
                    break
                
                remaining_clicks = min(self.clicks_per_session, 
                                     self.target_clicks - self.total_success)
                
                if remaining_clicks <= 0:
                    break
                
                future = executor.submit(self.worker_click_session, i, remaining_clicks)
                futures.append(future)
            
            # 結果収集
            for future in as_completed(futures):
                if self.stop_event.is_set():
                    break
                try:
                    result = future.result(timeout=self.session_timeout + 60)
                    self.result_queue.put(result)
                except Exception as e:
                    logger.error(f"ワーカーエラー: {e}")

def signal_handler(signum, frame):
    """シグナルハンドラ"""
    logger.info("🛑 終了シグナル受信")
    sys.exit(0)

def main():
    """メイン実行関数"""
    print("🎯 大規模広告クリックシステム")
    print("=" * 80)
    print()
    
    # シグナルハンドラ設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 設定
    target_clicks = 100000  # 10万クリック
    max_workers = None      # 自動設定
    use_multiprocessing = True  # マルチプロセス使用
    clicks_per_session = 2000   # セッションあたり2000クリック
    
    print(f"🎯 目標クリック数: {target_clicks:,}")
    print(f"💻 システム情報:")
    print(f"   CPU: {multiprocessing.cpu_count()} コア")
    print(f"   メモリ: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print()
    
    # 実行確認
    response = input("実行しますか？ (y/N): ").strip().lower()
    if response != 'y':
        print("❌ 実行をキャンセルしました")
        return
    
    try:
        # クリッカー初期化
        clicker = MassiveAdClicker(
            target_clicks=target_clicks,
            max_workers=max_workers,
            use_multiprocessing=use_multiprocessing,
            clicks_per_session=clicks_per_session
        )
        
        # 実行
        results = clicker.run_massive_clicking()
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f'massive_click_results_{timestamp}.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"📁 詳細結果: {results_file}")
        print(f"📝 実行ログ: massive_ad_click.log")
        
    except Exception as e:
        logger.error(f"❌ 致命的エラー: {e}")
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()