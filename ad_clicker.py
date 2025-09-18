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
    ElementClickInterceptedException
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
        広告リンクをクリック（iframe要素も処理）

        Args:
            link_info: リンク情報

        Returns:
            クリック成功かどうか
        """
        try:
            element = link_info['element']
            href = link_info['href']
            text = link_info['text']
            link_type = link_info.get('type', 'link')

            logger.info(f"クリック実行: {text} ({link_type}) -> {href}")

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
            
            # iframe自体をクリックする場合
            if link_type == 'iframe':
                # iframeまでスクロール
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(random.uniform(1, 2))

                # iframeの位置とサイズを取得
                location = element.location
                size = element.size

                # iframe内の中央をクリック
                try:
                    # iframeに切り替えてから内部をクリック
                    self.driver.switch_to.frame(element)
                    # iframe内のbodyまたは最初のクリック可能な要素を探す
                    body = self.driver.find_element(By.TAG_NAME, 'body')
                    ActionChains(self.driver).move_to_element(body).click().perform()
                    self.driver.switch_to.default_content()
                except:
                    # iframe切り替えに失敗した場合は、iframe要素自体をクリック
                    self.driver.switch_to.default_content()
                    ActionChains(self.driver).move_to_element(element).click().perform()
            else:
                # 通常の要素またはiframe内の要素をクリック
                # 要素まで自然にスクロール
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(random.uniform(1, 2))

                # 要素が見える状態かチェック
                if not element.is_displayed():
                    logger.warning(f"要素が見えません: {text}")
                    if link_type in ['iframe_link', 'iframe_image']:
                        self.driver.switch_to.default_content()
                    return False

                # 自然なマウス動作でクリック
                try:
                    ActionChains(self.driver).move_to_element(element).pause(0.5).click().perform()
                except ElementClickInterceptedException:
                    # JavaScriptでクリック
                    self.driver.execute_script("arguments[0].click();", element)

            # iframe内の要素をクリックした後は必ずメインフレームに戻る
            if link_type in ['iframe_link', 'iframe_image']:
                self.driver.switch_to.default_content()

            # クリック済みリストに追加
            self.clicked_links.add(href)

            # クリック後の待機（ページ遷移やポップアップを待つ）
            time.sleep(2)

            # 新しいタブが開いた場合の処理
            if len(self.driver.window_handles) > 1:
                # 新しいタブを閉じて元のタブに戻る
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(1)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                logger.info("新しいタブを閉じました")

            logger.info(f"クリック成功: {text}")
            return True
            
        except Exception as e:
            logger.error(f"クリックエラー: {e}")
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

def main():
    """メイン実行関数"""
    target_url = "https://kimagureokazu.com/stripchat-free-50coin-japan/"
    
    print("="*80)
    print("広告自動クリックスクリプト")
    print("="*80)
    print(f"対象URL: {target_url}")
    print()
    
    # 設定
    max_clicks = 15          # 最大クリック数
    session_duration = 600   # 10分間のセッション
    headless_mode = False    # ブラウザを表示（デバッグ用）
    
    # クリッカー初期化
    clicker = AdClicker(
        headless=headless_mode,
        delay_range=(3, 8)  # 3-8秒のランダム待機
    )
    
    # 実行
    try:
        results = clicker.run_ad_clicking(
            target_url=target_url,
            max_clicks=max_clicks,
            session_duration=session_duration
        )
        
        # 結果をファイルに保存
        import json
        with open('ad_click_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print()
        print("📊 クリック結果:")
        print(f"   成功: {results['successful_clicks']}/{results['total_clicks']}")
        print(f"   成功率: {results['success_rate']:.1f}%")
        print(f"   実行時間: {results['duration']:.1f}秒")
        print()
        print("📁 詳細結果: ad_click_results.json")
        print("📝 実行ログ: ad_clicker.log")
        
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによって中断されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()