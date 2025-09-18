#!/usr/bin/env python3
"""
分離型広告クリックスクリプト
site_url: アクセス対象のサイト
ad_url: 実際にクリックする広告URL
"""

import time
import json
import logging
import random
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    WebDriverException
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('separated_clicker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SeparatedUrlClicker:
    """分離型URL広告クリックエージェント"""
    
    def __init__(self, agent_id: int = 0, headless: bool = False, delay_range: tuple = (2, 5)):
        """
        初期化
        
        Args:
            agent_id: エージェントID
            headless: ヘッドレスモードで実行するか
            delay_range: クリック間隔のランダム範囲（秒）
        """
        self.agent_id = agent_id
        self.headless = headless
        self.delay_range = delay_range
        self.driver = None
        self.clicked_ads = set()  # クリック済み広告URLを記録
        
    def setup_driver(self) -> webdriver.Chrome:
        """WebDriverのセットアップ"""
        options = Options()
        
        # 基本オプション
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent設定（自然なアクセスを模倣）
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # 広告ブロッカーを無効化
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins-discovery')
        
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
        
        # WebDriver初期化
        driver_path = ChromeDriverManager().install()
        driver_dir = os.path.dirname(driver_path)
        actual_driver = os.path.join(driver_dir, 'chromedriver')
        if not os.path.exists(actual_driver):
            for file in os.listdir(driver_dir):
                if 'chromedriver' in file and not file.endswith('.chromedriver'):
                    actual_driver = os.path.join(driver_dir, file)
                    break
        
        service = Service(actual_driver)
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        
        # ボット検出回避のスクリプト実行
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def access_site(self, site_url: str) -> bool:
        """
        サイトにアクセス（広告表示のため）
        
        Args:
            site_url: アクセス対象のサイトURL
            
        Returns:
            アクセス成功かどうか
        """
        try:
            logger.info(f"Agent {self.agent_id}: サイトアクセス -> {site_url}")
            self.driver.get(site_url)
            
            # ページ読み込み完了を待機
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 追加の読み込み待機（広告読み込みのため）
            time.sleep(random.uniform(3, 6))
            
            # ページを少しスクロール（広告表示のトリガー）
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            
            logger.info(f"Agent {self.agent_id}: サイトアクセス成功")
            return True
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id}: サイトアクセスエラー -> {e}")
            return False
    
    def click_ad_url(self, ad_url: str, method: str = 'new_tab') -> bool:
        """
        指定された広告URLをクリック
        
        Args:
            ad_url: クリック対象の広告URL
            method: クリック方法 ('new_tab', 'same_tab', 'javascript')
            
        Returns:
            クリック成功かどうか
        """
        try:
            if ad_url in self.clicked_ads:
                logger.info(f"Agent {self.agent_id}: 既にクリック済み -> {ad_url}")
                return False
            
            logger.info(f"Agent {self.agent_id}: 広告URLクリック実行 -> {ad_url}")
            
            if method == 'new_tab':
                # 新しいタブで広告URLを開く
                self.driver.execute_script(f"window.open('{ad_url}', '_blank');")
                
                # 新しいタブに切り替え
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    time.sleep(random.uniform(2, 4))  # 広告ページでの滞在時間
                    
                    # 新しいタブを閉じて元のタブに戻る
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
            elif method == 'same_tab':
                # 同じタブで広告URLに移動
                current_url = self.driver.current_url
                self.driver.get(ad_url)
                time.sleep(random.uniform(2, 4))  # 広告ページでの滞在時間
                
                # 元のページに戻る
                self.driver.back()
                
            elif method == 'javascript':
                # JavaScriptで広告URLにアクセス（バックグラウンド）
                script = f"""
                var img = new Image();
                img.src = '{ad_url}';
                """
                self.driver.execute_script(script)
                
            # クリック済みに追加
            self.clicked_ads.add(ad_url)
            
            logger.info(f"Agent {self.agent_id}: 広告クリック成功 -> {ad_url}")
            return True
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id}: 広告クリックエラー -> {e}")
            return False
    
    def run_separated_session(self, site_urls: List[str], ad_urls: List[str], 
                             target_clicks: int, max_duration: int = 1800) -> Dict:
        """
        分離型セッションを実行
        
        Args:
            site_urls: アクセス対象のサイトURLリスト
            ad_urls: クリック対象の広告URLリスト
            target_clicks: 目標クリック数
            max_duration: 最大実行時間（秒）
            
        Returns:
            実行結果
        """
        start_time = time.time()
        session_results = {
            'agent_id': self.agent_id,
            'target_clicks': target_clicks,
            'actual_clicks': 0,
            'successful_clicks': 0,
            'site_accesses': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat(),
            'clicked_ads': [],
            'accessed_sites': []
        }
        
        try:
            # WebDriver起動
            self.driver = self.setup_driver()
            if not self.driver:
                session_results['errors'] += 1
                return session_results
            
            logger.info(f"Agent {self.agent_id}: 分離型セッション開始 (目標: {target_clicks}クリック)")
            
            while (session_results['successful_clicks'] < target_clicks and 
                   (time.time() - start_time) < max_duration):
                
                try:
                    # ランダムにサイトを選択してアクセス
                    site_url = random.choice(site_urls)
                    if self.access_site(site_url):
                        session_results['site_accesses'] += 1
                        session_results['accessed_sites'].append({
                            'url': site_url,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # サイトアクセス後の待機時間
                        time.sleep(random.uniform(2, 5))
                        
                        # 複数の広告をクリック
                        click_count = random.randint(1, min(3, len(ad_urls)))
                        selected_ads = random.sample(ad_urls, click_count)
                        
                        for ad_url in selected_ads:
                            if session_results['successful_clicks'] >= target_clicks:
                                break
                                
                            session_results['actual_clicks'] += 1
                            
                            # クリック方法をランダムに選択
                            click_methods = ['new_tab', 'javascript']
                            method = random.choice(click_methods)
                            
                            if self.click_ad_url(ad_url, method=method):
                                session_results['successful_clicks'] += 1
                                session_results['clicked_ads'].append({
                                    'url': ad_url,
                                    'method': method,
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                logger.info(f"Agent {self.agent_id}: 進捗 {session_results['successful_clicks']}/{target_clicks}")
                            
                            # クリック間隔
                            time.sleep(random.uniform(*self.delay_range))
                    
                    else:
                        session_results['errors'] += 1
                        time.sleep(5)  # エラー時の待機
                    
                    # サイト間の移動間隔
                    time.sleep(random.uniform(3, 8))
                    
                except WebDriverException as e:
                    session_results['errors'] += 1
                    logger.warning(f"Agent {self.agent_id}: WebDriverエラー - 再試行")
                    
                    # ドライバーを再起動
                    try:
                        if self.driver:
                            self.driver.quit()
                        self.driver = self.setup_driver()
                        if not self.driver:
                            break
                    except:
                        break
                        
                except Exception as e:
                    session_results['errors'] += 1
                    logger.error(f"Agent {self.agent_id}: 予期しないエラー -> {e}")
                    time.sleep(5)
            
            session_results['duration'] = time.time() - start_time
            session_results['end_time'] = datetime.now().isoformat()
            
            logger.info(f"Agent {self.agent_id}: セッション完了 - {session_results['successful_clicks']}クリック成功")
            
        except Exception as e:
            session_results['errors'] += 1
            logger.error(f"Agent {self.agent_id}: セッション実行エラー -> {e}")
            
        finally:
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
                
        return session_results

def separated_worker(agent_id: int, site_urls: List[str], ad_urls: List[str], 
                    target_clicks: int) -> Dict:
    """分離型ワーカープロセス"""
    try:
        clicker = SeparatedUrlClicker(agent_id=agent_id, headless=True)
        return clicker.run_separated_session(site_urls, ad_urls, target_clicks)
    except Exception as e:
        return {
            'agent_id': agent_id,
            'target_clicks': target_clicks,
            'actual_clicks': 0,
            'successful_clicks': 0,
            'site_accesses': 0,
            'errors': 1,
            'error_message': str(e),
            'duration': 0
        }

class SeparatedUrlController:
    """分離型URL制御システム"""
    
    def __init__(self, total_target: int = 10000, max_agents: int = 15):
        self.total_target = total_target
        self.max_agents = max_agents
        self.results = []
        
        # デフォルトURL設定
        self.default_site_urls = [
            "https://kimagureokazu.com/stripchat-free-50coin-japan/",
            "https://kimagureokazu.com/",
            # 他のサイトも追加可能
        ]
        
        self.default_ad_urls = [
            "https://stripchat.com/signup?utm_source=kimagureokazu&utm_medium=blog&utm_campaign=free50coin",
            "https://jp.stripchat.com/girls",
            "https://jp.stripchat.com/signup",
            # 他の広告URLも追加可能
        ]
    
    def run_separated_campaign(self, site_urls: Optional[List[str]] = None, 
                              ad_urls: Optional[List[str]] = None):
        """分離型キャンペーンを実行"""
        
        # デフォルトURL使用
        if site_urls is None:
            site_urls = self.default_site_urls
        if ad_urls is None:
            ad_urls = self.default_ad_urls
            
        logger.info("="*80)
        logger.info(f"分離型広告クリックキャンペーン開始")
        logger.info(f"目標総クリック数: {self.total_target:,}")
        logger.info(f"最大同時エージェント数: {self.max_agents}")
        logger.info(f"対象サイト数: {len(site_urls)}")
        logger.info(f"広告URL数: {len(ad_urls)}")
        logger.info("="*80)
        
        print("📋 URL設定:")
        print("【アクセス対象サイト】")
        for i, url in enumerate(site_urls, 1):
            print(f"  {i}. {url}")
        print()
        print("【クリック対象広告】") 
        for i, url in enumerate(ad_urls, 1):
            print(f"  {i}. {url}")
        print()
        
        start_time = time.time()
        total_successful_clicks = 0
        
        # エージェント別の目標クリック数を計算
        clicks_per_agent = max(1, self.total_target // self.max_agents)
        
        try:
            # 複数バッチで実行
            batch_size = min(5, self.max_agents)
            agent_id = 0
            
            while total_successful_clicks < self.total_target:
                current_batch_size = min(batch_size, self.max_agents)
                remaining_target = self.total_target - total_successful_clicks
                
                logger.info(f"バッチ実行開始: エージェント数={current_batch_size}, 残り目標={remaining_target}")
                
                # ThreadPoolExecutorで並列実行（プロセスプールは重いため）
                with ThreadPoolExecutor(max_workers=current_batch_size) as executor:
                    futures = []
                    for i in range(current_batch_size):
                        if total_successful_clicks >= self.total_target:
                            break
                        agent_target = min(clicks_per_agent, remaining_target)
                        if agent_target <= 0:
                            break
                            
                        future = executor.submit(separated_worker, agent_id, site_urls, ad_urls, agent_target)
                        futures.append(future)
                        agent_id += 1
                    
                    # 結果を収集
                    batch_results = []
                    for future in as_completed(futures, timeout=1800):
                        try:
                            result = future.result()
                            batch_results.append(result)
                            total_successful_clicks += result['successful_clicks']
                            
                            logger.info(f"Agent {result['agent_id']} 完了: "
                                      f"{result['successful_clicks']}/{result['target_clicks']} "
                                      f"(総計: {total_successful_clicks:,}/{self.total_target:,})")
                            
                        except Exception as e:
                            logger.error(f"エージェント実行エラー: {e}")
                
                self.results.extend(batch_results)
                
                # 進捗状況を表示
                progress = (total_successful_clicks / self.total_target) * 100
                elapsed_time = time.time() - start_time
                logger.info(f"進捗: {total_successful_clicks:,}/{self.total_target:,} "
                          f"({progress:.1f}%) - 経過時間: {elapsed_time/60:.1f}分")
                
                if total_successful_clicks < self.total_target:
                    time.sleep(10)
            
            # 最終結果の生成
            total_duration = time.time() - start_time
            self.generate_separated_report(total_successful_clicks, total_duration)
            
        except Exception as e:
            logger.error(f"キャンペーン実行エラー: {e}")
        
        return self.results
    
    def generate_separated_report(self, total_clicks: int, duration: float):
        """分離型レポートを生成"""
        
        # 統計計算
        total_agents = len(self.results)
        total_attempts = sum(r['actual_clicks'] for r in self.results)
        total_site_accesses = sum(r['site_accesses'] for r in self.results)
        total_errors = sum(r['errors'] for r in self.results)
        
        success_rate = (total_clicks / total_attempts * 100) if total_attempts > 0 else 0
        clicks_per_second = total_clicks / duration if duration > 0 else 0
        
        # レポート生成
        report = f"""
{"="*80}
分離型広告クリックキャンペーン - 最終結果
{"="*80}

📊 実行統計:
   目標クリック数: {self.total_target:,}
   実際のクリック数: {total_clicks:,}
   達成率: {(total_clicks/self.total_target*100):.1f}%
   
📈 パフォーマンス:
   総試行回数: {total_attempts:,}
   成功率: {success_rate:.1f}%
   サイトアクセス数: {total_site_accesses:,}
   実行時間: {duration/60:.1f}分
   クリック/秒: {clicks_per_second:.2f}
   
🤖 エージェント情報:
   使用エージェント数: {total_agents}
   平均クリック/エージェント: {total_clicks/total_agents:.1f}
   総エラー数: {total_errors}
   
🎯 分離型の利点:
   - サイトアクセスと広告クリックを明確に分離
   - 特定の広告URLに確実にアクセス
   - クリック方法を選択可能（新しいタブ/JavaScript）
   - より精密な広告効果測定が可能
   
{"="*80}
        """
        
        print(report)
        logger.info("分離型キャンペーン完了")
        
        # 詳細結果をJSONで保存
        separated_results = {
            'campaign_summary': {
                'type': 'separated_url_campaign',
                'target_clicks': self.total_target,
                'actual_clicks': total_clicks,
                'success_rate': success_rate,
                'total_agents': total_agents,
                'duration_minutes': duration / 60,
                'clicks_per_second': clicks_per_second,
                'completion_time': datetime.now().isoformat()
            },
            'url_configuration': {
                'site_urls': self.default_site_urls,
                'ad_urls': self.default_ad_urls
            },
            'agent_results': self.results
        }
        
        with open('separated_url_results.json', 'w', encoding='utf-8') as f:
            json.dump(separated_results, f, ensure_ascii=False, indent=2)
        
        logger.info("📁 詳細結果を separated_url_results.json に保存しました")

def main():
    """メイン実行関数"""
    print("🎯 分離型広告クリックシステム")
    print("=" * 50)
    print("site_url: アクセス対象サイト")
    print("ad_url: クリック対象広告")
    print()
    
    # 設定
    target_clicks = 10000
    max_agents = 15
    
    # カスタムURL設定（オプション）
    custom_site_urls = [
        "https://kimagureokazu.com/stripchat-free-50coin-japan/",
        # 他のサイトURLを追加可能
    ]
    
    custom_ad_urls = [
        "https://stripchat.com/signup?utm_source=kimagureokazu&utm_medium=blog&utm_campaign=free50coin",
        "https://jp.stripchat.com/girls",
        "https://jp.stripchat.com/signup",
        # 他の広告URLを追加可能
    ]
    
    print(f"目標: {target_clicks:,}クリック")
    print(f"最大エージェント数: {max_agents}")
    print()
    
    # 実行
    controller = SeparatedUrlController(
        total_target=target_clicks,
        max_agents=max_agents
    )
    
    try:
        results = controller.run_separated_campaign(
            site_urls=custom_site_urls,
            ad_urls=custom_ad_urls
        )
        print(f"\n✅ キャンペーン完了: {len(results)}エージェントが実行されました")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        logger.error(f"メイン実行エラー: {e}")

if __name__ == "__main__":
    main()