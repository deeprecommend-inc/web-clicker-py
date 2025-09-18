#!/usr/bin/env python3
"""
Google AdSense 広告自動クリックスクリプト
AdSense広告を検出して順番にクリック
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
import os

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('adsense_clicker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdSenseClicker:
    """Google AdSense 広告クリックエージェント"""
    
    def __init__(self, headless: bool = False, delay_range: tuple = (3, 8)):
        """
        初期化
        
        Args:
            headless: ヘッドレスモードで実行するか
            delay_range: クリック間隔のランダム範囲（秒）
        """
        self.headless = headless
        self.delay_range = delay_range
        self.driver = None
        self.clicked_ads = []  # クリック済み広告の記録
        
    def setup_driver(self) -> webdriver.Chrome:
        """WebDriverのセットアップ"""
        options = Options()
        
        # 基本オプション
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # SSL/証明書エラーの無視
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-ssl-false-start')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors-list')
        options.add_argument('--ignore-urlfetcher-cert-requests')
        options.add_argument('--accept-insecure-certs')
        
        # 安定性向上オプション
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=AutomationControlled')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-field-trial-config')
        options.add_argument('--disable-back-forward-cache')
        options.add_argument('--disable-default-apps')
        options.add_argument('--no-first-run')
        options.add_argument('--force-color-profile=srgb')
        options.add_argument('--metrics-recording-only')
        options.add_argument('--use-mock-keychain')
        options.add_argument('--disable-crash-reporter')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-dev-tools')
        options.add_argument('--disable-in-process-stack-traces')
        options.add_argument('--disable-component-update')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-translate')
        options.add_argument('--hide-scrollbars')
        options.add_argument('--mute-audio')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--no-pings')
        options.add_argument('--single-process')  # シングルプロセスモード
        # options.add_argument('--remote-debugging-port=9222')  # DevTools接続維持（コメントアウト）
        
        # User-Agent設定
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # 広告ブロッカーを無効化（重要）
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins-discovery')
        prefs = {
            "profile.default_content_setting_values.plugins": 1,
            "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
            "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
            "PluginsAllowedForUrls": "*"
        }
        options.add_experimental_option("prefs", prefs)
        
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
        
        # WebDriver初期化
        driver_path = ChromeDriverManager().install()
        
        # ChromeDriverの実際のパスを特定
        if 'chromedriver-linux64' in driver_path:
            # 新しい形式のパス構造
            driver_dir = os.path.dirname(driver_path)
            actual_driver = os.path.join(driver_dir, 'chromedriver-linux64', 'chromedriver')
        else:
            # 従来の形式
            driver_dir = os.path.dirname(driver_path) 
            actual_driver = os.path.join(driver_dir, 'chromedriver')
            
        # ファイルが存在しない場合は検索
        if not os.path.exists(actual_driver):
            for root, dirs, files in os.walk(os.path.dirname(driver_path)):
                for file in files:
                    if file == 'chromedriver':
                        actual_driver = os.path.join(root, file)
                        break
                if os.path.exists(actual_driver):
                    break
        
        # 実行権限を確認・設定
        if os.path.exists(actual_driver):
            os.chmod(actual_driver, 0o755)
            logger.info(f"ChromeDriver path: {actual_driver}")
        else:
            logger.error(f"ChromeDriver not found at {actual_driver}")
            
        service = Service(actual_driver)
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        
        # ボット検出回避
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def detect_adsense_ads(self) -> List[Dict]:
        """
        Google AdSense 広告を検出
        
        Returns:
            検出された広告のリスト
        """
        adsense_ads = []
        
        try:
            logger.info("AdSense広告の検出開始")
            
            # 現在のページURLとタイトルをログ
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"広告検出対象ページ: {current_url}")
            logger.info(f"ページタイトル: {page_title}")
            
            # ページソースの一部を確認（デバッグ用）
            page_source_snippet = self.driver.page_source[:1000]
            logger.info(f"ページソース（最初の1000文字）: {page_source_snippet}")
            
            # アクセス制限やボット検出がある場合の対処
            if any(keyword in page_title.lower() for keyword in ['access', 'notification', 'blocked', 'verification', 'captcha']):
                logger.warning(f"アクセス制限またはボット検出の可能性: {page_title}")
                
                # CAPTCHAやアクセス確認ボタンを探す
                proceed_buttons = [
                    'button:contains("Continue")',
                    'button:contains("Proceed")', 
                    'button:contains("続行")',
                    'button:contains("確認")',
                    'input[type="submit"]',
                    'button[type="submit"]',
                    '.btn',
                    '.button',
                    'a[href*="continue"]'
                ]
                
                for selector in proceed_buttons:
                    try:
                        if ':contains(' in selector:
                            # XPathを使用してテキストで検索
                            text_part = selector.split('(')[1].split(')')[0].strip('"')
                            xpath = f"//button[contains(text(), '{text_part}')] | //input[@value='{text_part}']"
                            buttons = self.driver.find_elements(By.XPATH, xpath)
                        else:
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                        for button in buttons:
                            if button.is_displayed():
                                logger.info(f"アクセス確認ボタンをクリック: {selector}")
                                button.click()
                                time.sleep(3)
                                new_title = self.driver.title
                                if new_title != page_title:
                                    logger.info(f"ページが変更されました: {page_title} -> {new_title}")
                                    break
                    except Exception as e:
                        logger.debug(f"ボタン検索エラー {selector}: {e}")
                        continue
            
            # 1. ins要素でAdSense広告を検出
            ins_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ins.adsbygoogle')
            logger.info(f"検出されたins.adsbygoogle要素: {len(ins_elements)}個")
            
            # 検出された要素の詳細をログ
            if ins_elements:
                for i, ins in enumerate(ins_elements[:3]):  # 最初の3つだけ詳細表示
                    try:
                        is_displayed = ins.is_displayed()
                        data_ad_slot = ins.get_attribute('data-ad-slot')
                        data_ad_client = ins.get_attribute('data-ad-client')
                        logger.info(f"ins[{i}]: displayed={is_displayed}, slot={data_ad_slot}, client={data_ad_client}")
                    except Exception as e:
                        logger.debug(f"ins[{i}]の詳細取得エラー: {e}")
            else:
                logger.warning("ins.adsbygoogle要素が見つかりません")
            
            for idx, ins in enumerate(ins_elements):
                try:
                    # 広告が表示されているかチェック
                    if ins.is_displayed():
                        # data-ad-slotなどの属性を取得
                        ad_slot = ins.get_attribute('data-ad-slot') or f'ins_{idx}'
                        ad_client = ins.get_attribute('data-ad-client') or ''
                        ad_format = ins.get_attribute('data-ad-format') or 'auto'
                        
                        adsense_ads.append({
                            'element': ins,
                            'type': 'ins_adsbygoogle',
                            'ad_slot': ad_slot,
                            'ad_client': ad_client,
                            'ad_format': ad_format,
                            'index': idx,
                            'selector': f'ins.adsbygoogle[{idx}]'
                        })
                        logger.info(f"AdSense広告検出 (ins): slot={ad_slot}, format={ad_format}")
                except Exception as e:
                    logger.debug(f"ins要素 {idx} の処理エラー: {e}")
            
            # 2. Google広告用のiframeを検出
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            logger.info(f"検出されたiframe総数: {len(iframes)}個")
            
            for idx, iframe in enumerate(iframes):
                try:
                    iframe_id = iframe.get_attribute('id') or ''
                    iframe_name = iframe.get_attribute('name') or ''
                    iframe_src = iframe.get_attribute('src') or ''
                    iframe_title = iframe.get_attribute('title') or ''
                    
                    # Google AdSense関連のiframeかチェック
                    is_adsense = any([
                        'google' in iframe_id.lower(),
                        'google' in iframe_name.lower(),
                        'googlesyndication' in iframe_src,
                        'doubleclick' in iframe_src,
                        'google' in iframe_src,
                        'googleads' in iframe_src,
                        'google_ads' in iframe_id.lower(),
                        'google_ads' in iframe_name.lower(),
                        'aswift' in iframe_id,  # Google AdSense特有のID
                        'aswift' in iframe_name,
                        'advertisement' in iframe_title.lower(),
                        'ad' == iframe_title.lower(),
                        iframe_title == ''  # タイトルが空のiframeも広告の可能性
                    ])
                    
                    if is_adsense and iframe.is_displayed():
                        # iframe内の広告を検出
                        adsense_ads.append({
                            'element': iframe,
                            'type': 'iframe_adsense',
                            'iframe_id': iframe_id,
                            'iframe_name': iframe_name,
                            'iframe_src': iframe_src[:100] if iframe_src else '',
                            'index': idx,
                            'selector': f'iframe[{idx}]'
                        })
                        logger.info(f"AdSense広告検出 (iframe): id={iframe_id}, name={iframe_name}")
                        
                except Exception as e:
                    logger.debug(f"iframe {idx} の処理エラー: {e}")
            
            # 3. div要素でAdSense広告を検出（コンテナ）
            ad_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                'div[id*="google_ads"], div[id*="div-gpt-ad"], div[class*="google-ad"], div[class*="adsense"]')
            
            logger.info(f"検出された広告コンテナ: {len(ad_containers)}個")
            
            for idx, container in enumerate(ad_containers):
                try:
                    if container.is_displayed():
                        container_id = container.get_attribute('id') or f'container_{idx}'
                        container_class = container.get_attribute('class') or ''
                        
                        # コンテナ内のクリック可能な要素を探す
                        clickable_elements = container.find_elements(By.CSS_SELECTOR, 'a, img, iframe, ins')
                        
                        if clickable_elements:
                            adsense_ads.append({
                                'element': container,
                                'type': 'div_container',
                                'container_id': container_id,
                                'container_class': container_class,
                                'clickable_count': len(clickable_elements),
                                'index': idx,
                                'selector': f'div#{container_id}' if 'container_' not in container_id else f'div[{idx}]'
                            })
                            logger.info(f"AdSense広告コンテナ検出: id={container_id}, clickable={len(clickable_elements)}")
                            
                except Exception as e:
                    logger.debug(f"コンテナ {idx} の処理エラー: {e}")
            
            # 4. Google Publisher Tag (GPT) 広告を検出
            gpt_slots = self.driver.find_elements(By.CSS_SELECTOR, 'div[id^="div-gpt-ad"]')
            logger.info(f"検出されたGPT広告スロット: {len(gpt_slots)}個")
            
            for idx, slot in enumerate(gpt_slots):
                try:
                    if slot.is_displayed():
                        slot_id = slot.get_attribute('id')
                        adsense_ads.append({
                            'element': slot,
                            'type': 'gpt_slot',
                            'slot_id': slot_id,
                            'index': idx,
                            'selector': f'div#{slot_id}'
                        })
                        logger.info(f"GPT広告スロット検出: id={slot_id}")
                except Exception as e:
                    logger.debug(f"GPTスロット {idx} の処理エラー: {e}")
            
            # 5. 一般的な広告要素も検出（fallback）
            if len(adsense_ads) == 0:
                logger.info("標準的なAdSense要素が見つからないため、一般的な広告要素を検索")
                
                # より広範囲な広告関連セレクタ
                fallback_selectors = [
                    'div[id*="ad"]',
                    'div[class*="ad"]', 
                    'div[id*="banner"]',
                    'div[class*="banner"]',
                    'iframe[src*="google"]',
                    'iframe[src*="doubleclick"]',
                    'iframe[name*="google"]',
                    'script[src*="googlesyndication"]',  # AdSenseスクリプト
                    'script[src*="googletagservices"]',   # Google Publisher Tag
                ]
                
                for selector in fallback_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            logger.info(f"Fallback検索 - {selector}: {len(elements)}個の要素")
                            
                            for idx, element in enumerate(elements[:5]):  # 最大5個まで
                                try:
                                    if element.is_displayed():
                                        element_id = element.get_attribute('id') or f'fallback_{selector}_{idx}'
                                        element_class = element.get_attribute('class') or ''
                                        element_src = element.get_attribute('src') or ''
                                        
                                        adsense_ads.append({
                                            'element': element,
                                            'type': 'fallback_ad',
                                            'selector': selector,
                                            'element_id': element_id,
                                            'element_class': element_class,
                                            'element_src': element_src[:100] if element_src else '',
                                            'index': idx
                                        })
                                        logger.info(f"Fallback広告検出: {selector} - id={element_id}")
                                except Exception as e:
                                    logger.debug(f"Fallback要素 {idx} の処理エラー: {e}")
                                    
                    except Exception as e:
                        logger.debug(f"Fallbackセレクタ {selector} のエラー: {e}")
            
            logger.info(f"合計 {len(adsense_ads)} 個の広告要素を検出")
            
            # 検出された広告の概要をログ出力
            if adsense_ads:
                type_counts = {}
                for ad in adsense_ads:
                    ad_type = ad['type']
                    type_counts[ad_type] = type_counts.get(ad_type, 0) + 1
                
                logger.info("検出された広告タイプ別カウント:")
                for ad_type, count in type_counts.items():
                    logger.info(f"  {ad_type}: {count}個")
            else:
                logger.warning("WARNING - 広告がみつかりませんでした")
                
            return adsense_ads
            
        except Exception as e:
            logger.error(f"AdSense広告検出エラー: {e}")
            return []
    
    def click_adsense_ad(self, ad_info: Dict) -> bool:
        """
        AdSense広告をクリック
        
        Args:
            ad_info: 広告情報
            
        Returns:
            クリック成功かどうか
        """
        try:
            element = ad_info['element']
            ad_type = ad_info['type']
            
            logger.info(f"AdSense広告クリック実行: type={ad_type}, index={ad_info.get('index')}")
            
            # 要素までスクロール
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(random.uniform(1, 2))
            
            # 広告タイプ別のクリック処理
            if ad_type == 'iframe_adsense':
                # iframe内の広告をクリック
                try:
                    # iframeに切り替え
                    self.driver.switch_to.frame(element)
                    
                    # iframe内でクリック可能な要素を探す
                    clickable = None
                    
                    # リンクを探す
                    links = self.driver.find_elements(By.TAG_NAME, 'a')
                    if links:
                        clickable = links[0]
                    
                    # リンクがなければ画像を探す
                    if not clickable:
                        images = self.driver.find_elements(By.TAG_NAME, 'img')
                        if images:
                            clickable = images[0]
                    
                    # それでもなければbody全体をクリック
                    if not clickable:
                        clickable = self.driver.find_element(By.TAG_NAME, 'body')
                    
                    if clickable:
                        ActionChains(self.driver).move_to_element(clickable).click().perform()
                        logger.info(f"iframe内広告クリック成功")
                    
                    # メインフレームに戻る
                    self.driver.switch_to.default_content()
                    
                except Exception as e:
                    logger.warning(f"iframe広告クリックエラー: {e}")
                    self.driver.switch_to.default_content()
                    # iframe自体をクリック
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    
            elif ad_type == 'ins_adsbygoogle':
                # ins要素の広告をクリック
                # ins要素自体はクリックできないので、内部の要素を探す
                clickable_children = element.find_elements(By.CSS_SELECTOR, 'iframe, a, img')
                
                if clickable_children:
                    # 最初の子要素をクリック
                    ActionChains(self.driver).move_to_element(clickable_children[0]).click().perform()
                else:
                    # 子要素がなければins要素自体をクリック
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    
            elif ad_type == 'div_container':
                # コンテナ内のクリック可能な要素を探す
                clickable = element.find_elements(By.CSS_SELECTOR, 'a, img, iframe')
                
                if clickable:
                    # 最初のクリック可能要素をクリック
                    ActionChains(self.driver).move_to_element(clickable[0]).click().perform()
                else:
                    # なければコンテナ自体をクリック
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    
            elif ad_type == 'gpt_slot':
                # GPT広告スロットをクリック
                # 通常はiframeが内部にある
                iframes = element.find_elements(By.TAG_NAME, 'iframe')
                if iframes:
                    # iframe内をクリック
                    self.driver.switch_to.frame(iframes[0])
                    body = self.driver.find_element(By.TAG_NAME, 'body')
                    ActionChains(self.driver).move_to_element(body).click().perform()
                    self.driver.switch_to.default_content()
                else:
                    ActionChains(self.driver).move_to_element(element).click().perform()
            
            elif ad_type == 'fallback_ad':
                # Fallback広告要素のクリック
                element_tag = element.tag_name.lower()
                
                if element_tag == 'script':
                    # script要素は直接クリックできないので、親要素を探す
                    try:
                        parent = element.find_element(By.XPATH, '..')
                        ActionChains(self.driver).move_to_element(parent).click().perform()
                    except:
                        logger.warning("script要素の親要素をクリックできませんでした")
                        return False
                elif element_tag == 'iframe':
                    # iframe内をクリック
                    try:
                        self.driver.switch_to.frame(element)
                        body = self.driver.find_element(By.TAG_NAME, 'body')
                        ActionChains(self.driver).move_to_element(body).click().perform()
                        self.driver.switch_to.default_content()
                    except:
                        self.driver.switch_to.default_content()
                        ActionChains(self.driver).move_to_element(element).click().perform()
                else:
                    # 通常のdiv等の要素
                    # 内部にリンクがあるかチェック
                    links = element.find_elements(By.TAG_NAME, 'a')
                    if links:
                        ActionChains(self.driver).move_to_element(links[0]).click().perform()
                    else:
                        ActionChains(self.driver).move_to_element(element).click().perform()
            
            else:
                # その他の場合は直接クリック
                ActionChains(self.driver).move_to_element(element).click().perform()
            
            # クリック後の待機
            time.sleep(2)
            
            # 新しいタブが開いた場合の処理
            if len(self.driver.window_handles) > 1:
                # 新しいタブに切り替え
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(random.uniform(3, 6))  # 広告ページでの滞在
                
                # 広告ページのURLを記録
                ad_url = self.driver.current_url
                logger.info(f"広告ページ: {ad_url}")
                
                # タブを閉じて元に戻る
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                logger.info("広告タブを閉じました")
            
            # クリック済みに記録
            self.clicked_ads.append({
                'type': ad_type,
                'timestamp': datetime.now().isoformat(),
                'details': ad_info
            })
            
            logger.info(f"AdSense広告クリック成功: {ad_type}")
            return True
            
        except Exception as e:
            logger.error(f"AdSense広告クリックエラー: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False
    
    def click_all_adsense_sequentially(self, url: str, max_clicks: int = 10) -> Dict:
        """
        ページ内のAdSense広告を順番にクリック
        
        Args:
            url: 対象ページURL
            max_clicks: 最大クリック数
            
        Returns:
            実行結果
        """
        start_time = datetime.now()
        results = {
            'url': url,
            'start_time': start_time.isoformat(),
            'detected_ads': 0,
            'successful_clicks': 0,
            'failed_clicks': 0,
            'clicked_ads': [],
            'errors': []
        }
        
        try:
            # WebDriver起動
            self.driver = self.setup_driver()
            
            logger.info(f"ページアクセス: {url}")
            self.driver.get(url)
            
            # ページ読み込み待機
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                logger.warning("ページ読み込みタイムアウト - 続行します")
            
            # プライバシーエラーページの確認と処理
            page_title = self.driver.title
            if "Privacy error" in page_title or "証明書" in page_title or "SSL" in page_title:
                logger.warning(f"プライバシーエラーページを検出: {page_title}")
                
                # 「詳細設定」や「続行」ボタンを探してクリック
                advance_buttons = [
                    'button[id*="details"]',
                    'button[id*="advanced"]', 
                    'a[id*="proceed"]',
                    'button[id*="proceed"]',
                    'a[id*="unsafe"]',
                    '#details-button',
                    '#proceed-link',
                    '#advanced-button'
                ]
                
                for selector in advance_buttons:
                    try:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed():
                            logger.info(f"'{selector}'ボタンをクリックして続行を試行")
                            button.click()
                            time.sleep(2)
                            break
                    except:
                        continue
                
                # 再度ページタイトルをチェック
                new_title = self.driver.title
                if new_title != page_title:
                    logger.info(f"ページが変更されました: {new_title}")
                else:
                    logger.warning("プライバシーエラーページから進めませんでした")
            
            # 追加待機（広告読み込みのため）
            time.sleep(5)
            
            # より保守的なスクロール（広告を表示させる）
            logger.info("ページスクロールで広告を表示")
            try:
                # まず基本的な接続チェック
                page_height = self.driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.offsetHeight);")
                logger.info(f"ページ高さ: {page_height}px")
                
                # 小刻みにスクロール（クラッシュを避けるため）
                scroll_steps = [0, 500, 1000, 1500, 2000]
                for i, scroll_y in enumerate(scroll_steps):
                    try:
                        # 現在のスクロール位置を取得してログ
                        current_scroll = self.driver.execute_script("return window.pageYOffset;")
                        
                        # 段階的にスクロール
                        actual_scroll = min(scroll_y, page_height - 1000)  # ページ末尾まで行かないように
                        if actual_scroll > current_scroll:
                            self.driver.execute_script(f"window.scrollTo({{top: {actual_scroll}, behavior: 'smooth'}});")
                            time.sleep(3)  # より長い待機時間
                            logger.info(f"スクロール {i+1}/{len(scroll_steps)}: {actual_scroll}px")
                        else:
                            logger.info(f"スクロール {i+1}: すでに十分にスクロール済み")
                            break
                            
                    except WebDriverException as e:
                        logger.warning(f"スクロール中のWebDriverエラー: {e}")
                        if "session deleted" in str(e) or "chrome not reachable" in str(e):
                            logger.error("ブラウザセッションが切断されました")
                            raise WebDriverException("Browser session lost during scrolling")
                        break
                    except Exception as e:
                        logger.warning(f"スクロール中のエラー: {e}")
                        break
                
                # 最後にトップに戻る
                try:
                    self.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
                    time.sleep(2)
                    logger.info("スクロール完了、トップに戻りました")
                except Exception as e:
                    logger.warning(f"トップへのスクロールエラー: {e}")
                    
            except Exception as e:
                logger.warning(f"スクロール処理全体でエラー: {e}")
                # スクロールに失敗してもad検出は試行する
            
            # AdSense広告を検出
            adsense_ads = self.detect_adsense_ads()
            results['detected_ads'] = len(adsense_ads)
            
            if not adsense_ads:
                logger.warning("AdSense広告が見つかりません")
                results['errors'].append("No AdSense ads detected")
            else:
                logger.info(f"{len(adsense_ads)}個のAdSense広告を順番にクリックします")
                
                # 順番にクリック
                click_count = 0
                for i, ad in enumerate(adsense_ads):
                    if click_count >= max_clicks:
                        logger.info(f"最大クリック数 {max_clicks} に到達")
                        break
                    
                    logger.info(f"広告 {i+1}/{len(adsense_ads)} をクリック中...")
                    
                    if self.click_adsense_ad(ad):
                        results['successful_clicks'] += 1
                        results['clicked_ads'].append({
                            'index': i,
                            'type': ad['type'],
                            'timestamp': datetime.now().isoformat()
                        })
                        click_count += 1
                        
                        # クリック間隔
                        delay = random.uniform(*self.delay_range)
                        logger.info(f"次のクリックまで {delay:.1f}秒 待機")
                        time.sleep(delay)
                    else:
                        results['failed_clicks'] += 1
                        logger.warning(f"広告 {i+1} のクリックに失敗")
            
            # 最終結果
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration'] = (end_time - start_time).total_seconds()
            
            logger.info("="*60)
            logger.info("AdSenseクリック完了")
            logger.info(f"検出された広告: {results['detected_ads']}")
            logger.info(f"成功クリック: {results['successful_clicks']}")
            logger.info(f"失敗クリック: {results['failed_clicks']}")
            logger.info(f"実行時間: {results['duration']:.1f}秒")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            results['errors'].append(str(e))
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return results

def main():
    """メイン実行関数"""
    
    # テスト用URL（AdSense広告があるページ）
    test_urls = [
        "https://kimagureokazu.com/stripchat-free-50coin-japan/",
        # 他のAdSense広告があるページURLを追加可能
    ]
    
    print("🎯 Google AdSense 広告自動クリックシステム")
    print("=" * 60)
    print()
    
    # 設定
    max_clicks_per_page = 5  # ページあたりの最大クリック数
    headless_mode = True      # ヘッドレスモード（安定性のため）
    
    # AdSenseクリッカー初期化
    clicker = AdSenseClicker(
        headless=headless_mode,
        delay_range=(3, 8)  # 3-8秒のランダム待機
    )
    
    all_results = []
    
    for url in test_urls:
        print(f"📍 処理中: {url}")
        print()
        
        try:
            # AdSense広告を順番にクリック
            results = clicker.click_all_adsense_sequentially(
                url=url,
                max_clicks=max_clicks_per_page
            )
            
            all_results.append(results)
            
            # 結果表示
            print(f"✅ 完了: {url}")
            print(f"   検出: {results['detected_ads']}個")
            print(f"   成功: {results['successful_clicks']}クリック")
            print(f"   失敗: {results['failed_clicks']}クリック")
            print()
            
            # ページ間の待機
            if url != test_urls[-1]:
                wait_time = random.uniform(5, 10)
                print(f"⏳ 次のページまで {wait_time:.1f}秒 待機...")
                time.sleep(wait_time)
                print()
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            print()
    
    # 全体結果を保存
    with open('adsense_click_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print("="*60)
    print("📊 全体結果:")
    total_detected = sum(r['detected_ads'] for r in all_results)
    total_success = sum(r['successful_clicks'] for r in all_results)
    total_failed = sum(r['failed_clicks'] for r in all_results)
    
    print(f"   総検出数: {total_detected}個")
    print(f"   総成功数: {total_success}クリック")
    print(f"   総失敗数: {total_failed}クリック")
    print()
    print("📁 詳細結果: adsense_click_results.json")
    print("📝 実行ログ: adsense_clicker.log")
    print("="*60)

if __name__ == "__main__":
    main()