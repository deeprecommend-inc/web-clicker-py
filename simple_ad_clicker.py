#!/usr/bin/env python3
"""
シンプルな広告クリックスクリプト
より安定したブラウザ制御で広告を検出してクリック
"""

import time
import json
import logging
import random
from typing import List, Dict, Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import *
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAdClicker:
    """シンプルな広告クリッカー"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.clicked_count = 0
        
    def setup_driver(self):
        """Chrome Driverのセットアップ"""
        options = Options()
        
        # 基本オプション（最小限）
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # ウィンドウサイズ設定
        options.add_argument('--window-size=1920,1080')
        
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
        
        # ChromeDriverを取得
        driver_path = ChromeDriverManager().install()
        driver_dir = os.path.dirname(driver_path)
        
        # chromedriverの実際のパスを見つける
        actual_driver = None
        for file in os.listdir(driver_dir):
            if 'chromedriver' in file and os.path.isfile(os.path.join(driver_dir, file)):
                if not file.endswith('.exe'):  # Windows用実行ファイルを除外
                    actual_driver = os.path.join(driver_dir, file)
                    break
        
        if actual_driver:
            os.chmod(actual_driver, 0o755)  # 実行権限を付与
        else:
            raise Exception("ChromeDriver not found")
        
        service = Service(actual_driver)
        self.driver = webdriver.Chrome(service=service, options=options)
        logger.info("ブラウザを起動しました")
        
    def find_ads(self) -> List[Dict]:
        """広告要素を検出"""
        ads = []
        
        try:
            # 一般的な広告セレクタ
            ad_selectors = [
                # Google AdSense
                'ins.adsbygoogle',
                'iframe[id*="google_ads"]',
                'div[id*="google_ads"]',
                'div[id*="div-gpt-ad"]',
                
                # 一般的な広告クラス
                '.advertisement',
                '.ad-container',
                '.ad-wrapper',
                '.banner-ad',
                '[class*="ad-slot"]',
                '[class*="adsense"]',
                
                # iframe広告
                'iframe[src*="doubleclick"]',
                'iframe[src*="googlesyndication"]',
                'iframe[title="Advertisement"]',
                'iframe[title="ad"]',
                
                # 広告リンク
                'a[href*="doubleclick"]',
                'a[href*="googleadservices"]',
            ]
            
            for selector in ad_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for idx, element in enumerate(elements):
                        if element.is_displayed() and element.size['height'] > 50:
                            ads.append({
                                'element': element,
                                'selector': selector,
                                'index': idx,
                                'tag': element.tag_name
                            })
                            logger.info(f"広告検出: {selector} [{idx}]")
                except Exception as e:
                    logger.debug(f"セレクタ {selector} でエラー: {e}")
            
            logger.info(f"合計 {len(ads)} 個の広告を検出")
            return ads
            
        except Exception as e:
            logger.error(f"広告検出エラー: {e}")
            return []
    
    def click_ad(self, ad_info: Dict) -> bool:
        """広告をクリック"""
        try:
            element = ad_info['element']
            tag = ad_info['tag']
            
            # 要素までスクロール
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", 
                element
            )
            time.sleep(1)
            
            # クリック実行
            try:
                # 通常のクリック
                element.click()
                logger.info(f"広告クリック成功（通常）: {ad_info['selector']}")
            except:
                # JavaScriptでクリック
                self.driver.execute_script("arguments[0].click();", element)
                logger.info(f"広告クリック成功（JS）: {ad_info['selector']}")
            
            self.clicked_count += 1
            time.sleep(2)
            
            # 新しいタブが開いた場合の処理
            if len(self.driver.window_handles) > 1:
                # 最新のタブに切り替え
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info(f"新しいタブ: {self.driver.current_url[:50]}...")
                time.sleep(3)
                
                # タブを閉じて元に戻る
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            
            return True
            
        except Exception as e:
            logger.error(f"クリックエラー: {e}")
            return False
    
    def click_all_ads(self, url: str, max_clicks: int = 10):
        """ページ内の広告を順番にクリック"""
        logger.info(f"処理開始: {url}")
        
        try:
            # ブラウザを起動
            self.setup_driver()
            
            # ページにアクセス
            self.driver.get(url)
            logger.info("ページ読み込み中...")
            
            # 読み込み待機
            time.sleep(5)
            
            # ページを下までスクロール（広告を読み込ませる）
            logger.info("ページスクロール中...")
            last_height = 0
            for i in range(5):
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                self.driver.execute_script(f"window.scrollTo(0, {new_height * (i+1) / 5});")
                time.sleep(1)
            
            # トップに戻る
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 広告を検出
            ads = self.find_ads()
            
            if not ads:
                logger.warning("広告が見つかりませんでした")
                return
            
            # 順番にクリック
            for i, ad in enumerate(ads[:max_clicks]):
                logger.info(f"\n--- 広告 {i+1}/{min(len(ads), max_clicks)} をクリック ---")
                
                if self.click_ad(ad):
                    # ランダム待機
                    wait_time = random.uniform(3, 7)
                    logger.info(f"次のクリックまで {wait_time:.1f}秒 待機...")
                    time.sleep(wait_time)
            
            logger.info(f"\n完了: {self.clicked_count} 個の広告をクリックしました")
            
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("ブラウザを終了しました")

def main():
    """メイン関数"""
    print("\n🎯 シンプル広告クリッカー")
    print("=" * 50)
    
    # テストURL
    test_url = "https://kimagureokazu.com/stripchat-free-50coin-japan/"
    
    # クリッカー実行
    clicker = SimpleAdClicker(headless=False)  # デバッグ用に表示モード
    clicker.click_all_ads(test_url, max_clicks=5)
    
    print("\n✅ 処理完了")
    print("=" * 50)

if __name__ == "__main__":
    main()