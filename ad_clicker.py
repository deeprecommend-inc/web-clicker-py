#!/usr/bin/env python3
"""
広告自動クリックスクリプト
指定URLの広告リンク（aタグ）を自動でクリック
"""

import time
import logging
import random
from typing import List, Dict
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
        logging.FileHandler('ad_clicker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdClicker:
    """広告自動クリックエージェント"""
    
    def __init__(self, headless: bool = False, delay_range: tuple = (2, 5)):
        """
        初期化
        
        Args:
            headless: ヘッドレスモードで実行するか
            delay_range: クリック間隔のランダム範囲（秒）
        """
        self.headless = headless
        self.delay_range = delay_range
        self.driver = None
        self.clicked_links = set()  # クリック済みリンクを記録
        
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
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
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

    def find_iframe_ads(self) -> List[Dict]:
        """
        iframe内の広告を検出してクリック可能なリンクを返す

        Returns:
            iframe内の広告リンクのリスト
        """
        iframe_ads = []
        try:
            # すべてのiframeを取得
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            logger.info(f"検出されたiframe数: {len(iframes)}")

            for idx, iframe in enumerate(iframes):
                try:
                    # iframe属性をチェック（広告関連のiframeを特定）
                    iframe_src = iframe.get_attribute('src') or ''
                    iframe_id = iframe.get_attribute('id') or ''
                    iframe_class = iframe.get_attribute('class') or ''

                    # 広告関連のiframeかチェック
                    is_ad_iframe = any([
                        'ad' in iframe_src.lower(),
                        'ad' in iframe_id.lower(),
                        'ad' in iframe_class.lower(),
                        'banner' in iframe_src.lower(),
                        'banner' in iframe_id.lower(),
                        'banner' in iframe_class.lower(),
                        'shinobi' in iframe_src.lower(),
                        'admax' in iframe_src.lower(),
                        'doubleclick' in iframe_src.lower(),
                        'googlesyndication' in iframe_src.lower()
                    ])

                    if is_ad_iframe and iframe.is_displayed():
                        # iframeが表示されている場合、クリック可能な要素として追加
                        iframe_ads.append({
                            'element': iframe,
                            'href': iframe_src or f'iframe_{idx}',
                            'text': f'[iframe広告 {idx}]',
                            'type': 'iframe',
                            'selector': f'iframe[{idx}]',
                            'iframe_index': idx
                        })
                        logger.info(f"広告iframe検出: {iframe_src[:50] if iframe_src else f'iframe_{idx}'}")

                    # iframeの中身も検索
                    try:
                        # iframeに切り替え
                        self.driver.switch_to.frame(iframe)

                        # iframe内のリンクを検索
                        links = self.driver.find_elements(By.TAG_NAME, 'a')
                        images = self.driver.find_elements(By.TAG_NAME, 'img')

                        # クリック可能な要素を検索
                        for link in links:
                            try:
                                href = link.get_attribute('href')
                                if href and link.is_displayed():
                                    iframe_ads.append({
                                        'element': link,
                                        'href': href,
                                        'text': link.text.strip() or '[iframe内リンク]',
                                        'type': 'iframe_link',
                                        'selector': f'iframe[{idx}] a',
                                        'iframe_index': idx
                                    })
                            except:
                                pass

                        # クリック可能な画像を検索
                        for img in images:
                            try:
                                if img.is_displayed():
                                    # 親要素がリンクでない画像もクリック対象に
                                    parent = img.find_element(By.XPATH, '..')
                                    if parent.tag_name != 'a':
                                        iframe_ads.append({
                                            'element': img,
                                            'href': f'iframe_{idx}_img',
                                            'text': '[iframe内画像]',
                                            'type': 'iframe_image',
                                            'selector': f'iframe[{idx}] img',
                                            'iframe_index': idx
                                        })
                            except:
                                pass

                    except Exception as e:
                        logger.debug(f"iframe {idx} の中身を読み取れません: {e}")
                    finally:
                        # メインフレームに戻る
                        self.driver.switch_to.default_content()

                except Exception as e:
                    logger.debug(f"iframe {idx} の処理中にエラー: {e}")
                    # エラーが発生してもメインフレームに戻る
                    self.driver.switch_to.default_content()

        except Exception as e:
            logger.error(f"iframe広告検出エラー: {e}")
            # エラーが発生してもメインフレームに戻る
            self.driver.switch_to.default_content()

        return iframe_ads

    def find_ad_links(self, target_url: str) -> List[Dict]:
        """
        指定URLの広告リンクを検出（iframe内も含む）

        Args:
            target_url: 対象URL

        Returns:
            広告リンクのリスト
        """
        try:
            logger.info(f"ページアクセス: {target_url}")
            self.driver.get(target_url)

            # ページ読み込み待機
            time.sleep(3)

            # 広告リンクの候補を取得
            ad_links = []

            # まずiframe内の広告を検索
            ad_links.extend(self.find_iframe_ads())
            
            # 一般的な広告リンクのセレクタ
            ad_selectors = [
                'a[href*="chikayo-dsp.shinobi.jp/admax"]',  # 特定の広告配信システム
                'a[href*="shinobi.jp/admax"]',              # Shinobi AdMax広告
                'a[href*="stripchat"]',              # Stripchat関連リンク
                'a[href*="chaturbate"]',             # Chaturbate関連リンク
                'a[href*="cam"]',                    # カメラサイト関連
                'a[href*="affiliate"]',              # アフィリエイトリンク
                'a[href*="ref="]',                   # リファラルリンク
                'a[href*="utm_"]',                   # UTMパラメータ付きリンク
                'a.ad-link',                         # 広告リンククラス
                'a.affiliate-link',                  # アフィリエイトリンククラス
                'a.banner-link',                     # バナーリンククラス
                'a[target="_blank"]',                # 新しいタブで開くリンク
                'div.advertisement a',               # 広告エリア内のリンク
                'div.banner a',                      # バナーエリア内のリンク
                'div.promo a',                       # プロモエリア内のリンク
            ]
            
            # 各セレクタでリンクを検索
            for selector in ad_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            href = element.get_attribute('href')
                            text = element.text.strip()
                            is_visible = element.is_displayed()
                            
                            if href and href not in self.clicked_links and is_visible:
                                # 画像リンクかテキストリンクかを判定
                                img_tags = element.find_elements(By.TAG_NAME, 'img')
                                link_type = 'image' if img_tags else 'text'
                                
                                ad_links.append({
                                    'element': element,
                                    'href': href,
                                    'text': text or '[画像リンク]',
                                    'type': link_type,
                                    'selector': selector
                                })
                                
                        except StaleElementReferenceException:
                            continue
                            
                except Exception as e:
                    logger.debug(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            # 重複除去（同じhrefのリンクは1つだけ保持）
            unique_links = {}
            for link in ad_links:
                href = link['href']
                if href not in unique_links:
                    unique_links[href] = link
            
            ad_links = list(unique_links.values())
            
            logger.info(f"検出された広告リンク数: {len(ad_links)}")
            
            return ad_links
            
        except Exception as e:
            logger.error(f"広告リンク検出エラー: {e}")
            return []
    
    def click_ad_link(self, link_info: Dict) -> bool:
        """
        広告リンクをクリック（iframe要素も処理）- 高精度クリック処理

        Args:
            link_info: リンク情報

        Returns:
            クリック成功かどうか
        """
        element = link_info['element']
        href = link_info['href']
        text = link_info['text']
        link_type = link_info.get('type', 'link')

        logger.info(f"🎯 クリック実行: {text} ({link_type}) -> {href[:50]}...")

        try:
            # iframe内の要素の場合、先にiframeに切り替える
            if link_type in ['iframe_link', 'iframe_image']:
                iframe_index = link_info.get('iframe_index')
                if iframe_index is not None:
                    iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                    if iframe_index < len(iframes):
                        self.driver.switch_to.frame(iframes[iframe_index])
                        # iframe内で要素を再取得
                        if link_type == 'iframe_link':
                            elements = self.driver.find_elements(By.TAG_NAME, 'a')
                            for elem in elements:
                                if elem.get_attribute('href') == href:
                                    element = elem
                                    break
                        elif link_type == 'iframe_image':
                            elements = self.driver.find_elements(By.TAG_NAME, 'img')
                            if elements:
                                element = elements[0]  # 最初の画像を使用

            # 1. 要素までスクロールして待機
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)

            # 2. 要素の可視性と有効性を確保
            try:
                wait = WebDriverWait(self.driver, 5)
                wait.until(EC.element_to_be_clickable(element))
            except:
                pass

            # 3. 要素が見えるかチェックと強制表示
            if not element.is_displayed():
                self.driver.execute_script("""
                    arguments[0].style.display = 'block';
                    arguments[0].style.visibility = 'visible';
                    arguments[0].style.opacity = '1';
                    arguments[0].style.pointerEvents = 'auto';
                """, element)
                time.sleep(0.5)

            click_success = False
            click_method_used = ""

            if link_type == 'iframe':
                # iframe広告の処理
                click_success, click_method_used = self._handle_iframe_click(element)
            else:
                # 通常要素の処理
                click_success, click_method_used = self._handle_normal_click(element)

            # 4. クリック後の処理
            time.sleep(1)

            # iframe内の要素をクリックした後は必ずメインフレームに戻る
            if link_type in ['iframe_link', 'iframe_image']:
                self.driver.switch_to.default_content()

            # アラートの処理（成功の証明）
            alert_detected = False
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                logger.info(f"📢 アラート検出: {alert_text}")
                alert.accept()
                alert_detected = True
            except:
                pass

            # 新しいタブの処理（成功の証明）
            new_tab_opened = False
            if len(self.driver.window_handles) > 1:
                logger.info("🔗 新しいタブが開きました")
                new_tab_opened = True
                try:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    time.sleep(1)
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                except:
                    pass

            # 成功の判定（クリック成功またはアラートまたは新タブ）
            actual_success = click_success or alert_detected or new_tab_opened

            if actual_success:
                # クリック済みリストに追加
                self.clicked_links.add(href)
                logger.info(f"✅ クリック成功: {text} ({click_method_used})")
            else:
                logger.warning(f"❌ クリック失敗: {text}")

            return actual_success

        except Exception as e:
            logger.error(f"❌ クリックエラー ({text}): {e}")
            # エラーが発生してもメインフレームに戻る
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False
    
    def random_delay(self):
        """ランダムな待機時間"""
        delay = random.uniform(*self.delay_range)
        logger.info(f"待機: {delay:.2f}秒")
        time.sleep(delay)
    
    def _handle_iframe_click(self, element) -> tuple:
        """iframe要素のクリック処理"""
        # 方法1: iframe内の要素をクリック
        try:
            self.driver.switch_to.frame(element)
            
            # クリック可能な要素を順番に探す
            selectors = ['a', 'button', 'input[type="button"]', 'input[type="submit"]', '[onclick]', 'div', 'span', 'body']
            
            for selector in selectors:
                try:
                    clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if clickable_elements:
                        target = clickable_elements[0]
                        
                        # 複数のクリック方法を試す
                        for method_name, click_func in [
                            ('iframe内ActionChains', lambda: ActionChains(self.driver).move_to_element(target).click().perform()),
                            ('iframe内JavaScript', lambda: self.driver.execute_script("arguments[0].click();", target)),
                            ('iframe内direct', lambda: target.click())
                        ]:
                            try:
                                click_func()
                                self.driver.switch_to.default_content()
                                return True, method_name
                            except:
                                continue
                except:
                    continue
            
            self.driver.switch_to.default_content()
        except:
            try:
                self.driver.switch_to.default_content()
            except:
                pass
        
        # 方法2: iframe要素自体をクリック
        return self._handle_normal_click(element)
    
    def _handle_normal_click(self, element) -> tuple:
        """通常要素のクリック処理"""
        # 複数のクリック方法を順番に試す
        click_methods = [
            ('ActionChains移動クリック', lambda: ActionChains(self.driver).move_to_element(element).pause(0.5).click().perform()),
            ('ActionChains座標クリック', lambda: ActionChains(self.driver).move_to_element_with_offset(element, 1, 1).click().perform()),
            ('要素直接クリック', lambda: element.click()),
            ('JavaScript基本クリック', lambda: self.driver.execute_script("arguments[0].click();", element)),
            ('JavaScriptイベント発火', lambda: self.driver.execute_script(
                "var evt = new MouseEvent('click', {bubbles: true, cancelable: true, view: window}); arguments[0].dispatchEvent(evt);", element)),
            ('JavaScriptフォーカス+クリック', lambda: self.driver.execute_script(
                "arguments[0].focus(); arguments[0].click();", element)),
            ('JavaScript座標クリック', lambda: self._click_at_coordinates(element))
        ]
        
        for method_name, click_func in click_methods:
            try:
                click_func()
                logger.debug(f"✅ {method_name}でクリック成功")
                return True, method_name
            except Exception as e:
                logger.debug(f"❌ {method_name}失敗: {e}")
                continue
        
        return False, "全ての方法が失敗"
    
    def _click_at_coordinates(self, element):
        """要素の座標でクリック"""
        location = element.location
        size = element.size
        x = location['x'] + size['width'] / 2
        y = location['y'] + size['height'] / 2
        
        self.driver.execute_script(f"""
            var element = document.elementFromPoint({x}, {y});
            if (element) {{
                element.click();
            }}
        """)
    
    def run_ad_clicking(self, target_url: str, max_clicks: int = 10, session_duration: int = 300) -> Dict:
        """
        広告クリックセッションを実行
        
        Args:
            target_url: 対象URL
            max_clicks: 最大クリック数
            session_duration: セッション持続時間（秒）
            
        Returns:
            実行結果
        """
        start_time = datetime.now()
        results = {
            'start_time': start_time.isoformat(),
            'target_url': target_url,
            'clicked_links': [],
            'errors': [],
            'total_clicks': 0,
            'successful_clicks': 0
        }
        
        try:
            # WebDriver起動
            self.driver = self.setup_driver()
            session_end_time = time.time() + session_duration
            
            logger.info(f"広告クリックセッション開始: {target_url}")
            logger.info(f"最大クリック数: {max_clicks}, セッション時間: {session_duration}秒")
            
            while (time.time() < session_end_time and 
                   results['successful_clicks'] < max_clicks):
                
                # 広告リンクを検出
                ad_links = self.find_ad_links(target_url)
                
                if not ad_links:
                    logger.info("広告リンクが見つかりません。ページを再読み込みします。")
                    self.driver.refresh()
                    time.sleep(3)
                    continue
                
                # 未クリックのリンクをフィルタ
                unclicked_links = [
                    link for link in ad_links 
                    if link['href'] not in self.clicked_links
                ]
                
                if not unclicked_links:
                    logger.info("すべての広告リンクをクリック済み。ページを再読み込みします。")
                    self.driver.refresh()
                    time.sleep(3)
                    self.clicked_links.clear()  # クリック履歴をリセット
                    continue
                
                # ランダムにリンクを選択してクリック
                link_to_click = random.choice(unclicked_links)
                results['total_clicks'] += 1
                
                if self.click_ad_link(link_to_click):
                    results['successful_clicks'] += 1
                    results['clicked_links'].append({
                        'href': link_to_click['href'],
                        'text': link_to_click['text'],
                        'type': link_to_click['type'],
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    results['errors'].append({
                        'link': link_to_click['href'],
                        'error': 'クリック失敗',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # ランダム待機
                self.random_delay()
                
                # 残り時間をログ出力
                remaining_time = session_end_time - time.time()
                logger.info(f"進捗: {results['successful_clicks']}/{max_clicks}クリック, 残り時間: {remaining_time:.0f}秒")
            
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration'] = (end_time - start_time).total_seconds()
            results['success_rate'] = (results['successful_clicks'] / results['total_clicks'] * 100) if results['total_clicks'] > 0 else 0
            
            logger.info("="*60)
            logger.info("広告クリックセッション完了")
            logger.info(f"総クリック数: {results['total_clicks']}")
            logger.info(f"成功クリック数: {results['successful_clicks']}")
            logger.info(f"成功率: {results['success_rate']:.1f}%")
            logger.info(f"実行時間: {results['duration']:.1f}秒")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"セッション実行エラー: {e}")
            results['errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return results

    def run_massive_clicking(self, target_url: str, max_clicks: int = 100000) -> Dict:
        """
        大量クリックセッションを実行（10万回対応）
        
        Args:
            target_url: 対象URL
            max_clicks: 最大クリック数（デフォルト10万回）
            
        Returns:
            実行結果
        """
        start_time = datetime.now()
        results = {
            'start_time': start_time.isoformat(),
            'target_url': target_url,
            'max_clicks': max_clicks,
            'clicked_links': [],
            'errors': [],
            'total_clicks': 0,
            'successful_clicks': 0,
            'progress_milestones': []  # 進捗記録
        }
        
        try:
            # WebDriver起動
            self.driver = self.setup_driver()
            
            logger.info(f"🚀 大量広告クリックセッション開始: {target_url}")
            logger.info(f"目標クリック数: {max_clicks:,}回")
            
            click_count = 0
            consecutive_failures = 0
            max_consecutive_failures = 10
            
            while click_count < max_clicks:
                try:
                    # 広告リンクを検出
                    ad_links = self.find_ad_links(target_url)
                    
                    if not ad_links:
                        logger.info("広告リンクが見つかりません。ページを再読み込みします。")
                        self.driver.refresh()
                        time.sleep(3)
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error("連続してリンクが見つからないため中断します")
                            break
                        continue
                    
                    consecutive_failures = 0  # リセット
                    
                    # 未クリックのリンクをフィルタ
                    unclicked_links = [
                        link for link in ad_links 
                        if link['href'] not in self.clicked_links
                    ]
                    
                    if not unclicked_links:
                        logger.info("すべての広告リンクをクリック済み。ページを再読み込みします。")
                        self.driver.refresh()
                        time.sleep(3)
                        self.clicked_links.clear()  # クリック履歴をリセット
                        continue
                    
                    # 全てのリンクを順番にクリック（効率化）
                    for link_to_click in unclicked_links:
                        if click_count >= max_clicks:
                            break
                            
                        click_count += 1
                        results['total_clicks'] += 1
                        
                        if self.click_ad_link(link_to_click):
                            results['successful_clicks'] += 1
                            results['clicked_links'].append({
                                'href': link_to_click['href'],
                                'text': link_to_click['text'],
                                'type': link_to_click['type'],
                                'timestamp': datetime.now().isoformat(),
                                'click_number': click_count
                            })
                        else:
                            results['errors'].append({
                                'link': link_to_click['href'],
                                'error': 'クリック失敗',
                                'timestamp': datetime.now().isoformat(),
                                'click_number': click_count
                            })
                        
                        # 進捗ログ（1000回ごと）
                        if click_count % 1000 == 0:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            rate = click_count / elapsed if elapsed > 0 else 0
                            remaining = max_clicks - click_count
                            eta = remaining / rate if rate > 0 else 0
                            
                            milestone = {
                                'clicks': click_count,
                                'successful': results['successful_clicks'],
                                'success_rate': (results['successful_clicks'] / click_count * 100) if click_count > 0 else 0,
                                'elapsed_time': elapsed,
                                'clicks_per_second': rate,
                                'eta_seconds': eta,
                                'timestamp': datetime.now().isoformat()
                            }
                            results['progress_milestones'].append(milestone)
                            
                            logger.info(f"📊 進捗: {click_count:,}/{max_clicks:,} ({click_count/max_clicks*100:.1f}%)")
                            logger.info(f"   成功: {results['successful_clicks']:,} ({milestone['success_rate']:.1f}%)")
                            logger.info(f"   速度: {rate:.1f}クリック/秒, 残り時間: {eta/60:.1f}分")
                        
                        # 短い待機（効率化のため）
                        time.sleep(random.uniform(0.1, 0.3))
                    
                except KeyboardInterrupt:
                    logger.info("ユーザーによって中断されました")
                    break
                except Exception as e:
                    logger.error(f"セッション中エラー: {e}")
                    results['errors'].append({
                        'error': str(e),
                        'timestamp': datetime.now().isoformat(),
                        'click_number': click_count
                    })
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("連続エラーが多すぎるため中断します")
                        break
            
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration'] = (end_time - start_time).total_seconds()
            results['success_rate'] = (results['successful_clicks'] / results['total_clicks'] * 100) if results['total_clicks'] > 0 else 0
            results['clicks_per_second'] = results['total_clicks'] / results['duration'] if results['duration'] > 0 else 0
            
            logger.info("="*80)
            logger.info("🎯 大量広告クリックセッション完了")
            logger.info(f"📊 総クリック数: {results['total_clicks']:,}")
            logger.info(f"✅ 成功クリック数: {results['successful_clicks']:,}")
            logger.info(f"📈 成功率: {results['success_rate']:.1f}%")
            logger.info(f"⏱️ 実行時間: {results['duration']:.1f}秒 ({results['duration']/60:.1f}分)")
            logger.info(f"⚡ 平均速度: {results['clicks_per_second']:.1f}クリック/秒")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"セッション実行エラー: {e}")
            results['errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return results

def main():
    """メイン実行関数"""
    target_url = "https://kimagureokazu.com/stripchat-free-50coin-japan/"
    
    print("="*80)
    print("🚀 大量広告自動クリックスクリプト")
    print("="*80)
    print(f"対象URL: {target_url}")
    print()
    
    # 設定選択
    print("実行モードを選択してください:")
    print("1. 通常モード（15回）")
    print("2. 大量モード（10万回）")
    print("3. カスタムモード")
    
    mode = input("モードを選択 (1-3): ").strip()
    
    if mode == "1":
        max_clicks = 15
        session_duration = 600
        use_massive_mode = False
    elif mode == "2":
        max_clicks = 100000
        session_duration = None
        use_massive_mode = True
    elif mode == "3":
        try:
            max_clicks = int(input("クリック数を入力: "))
            use_massive_mode = max_clicks > 1000
            session_duration = None if use_massive_mode else 600
        except ValueError:
            print("無効な入力です。デフォルト設定を使用します。")
            max_clicks = 15
            session_duration = 600
            use_massive_mode = False
    else:
        print("無効な選択です。通常モードで実行します。")
        max_clicks = 15
        session_duration = 600
        use_massive_mode = False
    
    headless_mode = input("ヘッドレスモードで実行しますか？ (y/N): ").lower().startswith('y')
    
    print()
    print(f"設定: {max_clicks:,}回クリック, ヘッドレス: {headless_mode}")
    print()
    
    # クリッカー初期化
    clicker = AdClicker(
        headless=headless_mode,
        delay_range=(0.1, 0.5) if use_massive_mode else (3, 8)
    )
    
    # 実行
    try:
        if use_massive_mode:
            results = clicker.run_massive_clicking(
                target_url=target_url,
                max_clicks=max_clicks
            )
        else:
            results = clicker.run_ad_clicking(
                target_url=target_url,
                max_clicks=max_clicks,
                session_duration=session_duration
            )
        
        # 結果をファイルに保存
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'ad_click_results_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print()
        print("📊 最終結果:")
        print(f"   総クリック: {results['total_clicks']:,}")
        print(f"   成功: {results['successful_clicks']:,}")
        print(f"   成功率: {results['success_rate']:.1f}%")
        print(f"   実行時間: {results['duration']:.1f}秒 ({results['duration']/60:.1f}分)")
        if 'clicks_per_second' in results:
            print(f"   平均速度: {results['clicks_per_second']:.1f}クリック/秒")
        print()
        print(f"📁 詳細結果: {filename}")
        print("📝 実行ログ: ad_clicker.log")
        
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによって中断されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
