#!/usr/bin/env python3
"""
広告クリック機能テスト用スクリプト
様々なタイプの広告要素をテストページで検証
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
        logging.FileHandler('test_ad_click.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdClickTester:
    """広告クリック機能テスト用クラス"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.test_results = []
        
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
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-web-security')
        
        # 安定性向上オプション
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--single-process')
        
        # User-Agent設定
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
        
        # WebDriver初期化
        driver_path = ChromeDriverManager().install()
        
        # ChromeDriverの実際のパスを特定
        if 'chromedriver-linux64' in driver_path:
            driver_dir = os.path.dirname(driver_path)
            actual_driver = os.path.join(driver_dir, 'chromedriver-linux64', 'chromedriver')
        else:
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
        
        service = Service(actual_driver)
        driver = webdriver.Chrome(service=service, options=options)
        
        if not self.headless:
            driver.maximize_window()
        
        # ボット検出回避
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def create_test_html(self) -> str:
        """テスト用HTMLページを作成"""
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>広告クリックテストページ</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .ad-container { 
            border: 2px solid #ccc; 
            margin: 20px 0; 
            padding: 15px; 
            background-color: #f9f9f9; 
        }
        .ad-banner { 
            background-color: #ff6b6b; 
            color: white; 
            padding: 20px; 
            text-align: center; 
            cursor: pointer;
            border-radius: 5px;
        }
        .ad-iframe { 
            width: 300px; 
            height: 250px; 
            border: 1px solid #ddd; 
        }
        .btn { 
            background-color: #4CAF50; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            cursor: pointer; 
            border-radius: 3px;
        }
        .btn:hover { background-color: #45a049; }
        .ad-image { width: 300px; height: 200px; cursor: pointer; }
        h2 { color: #333; }
        .test-result { margin: 10px 0; padding: 5px; background-color: #e7f3ff; }
    </style>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0000000000000000" crossorigin="anonymous"></script>
</head>
<body>
    <h1>🎯 広告クリックテストページ</h1>
    <p>このページは広告クリック機能をテストするためのサンプルページです。</p>
    
    <h2>1. AdSense風ins要素</h2>
    <div class="ad-container">
        <ins class="adsbygoogle"
             data-ad-client="ca-pub-1234567890123456"
             data-ad-slot="1234567890"
             data-ad-format="auto"
             style="display:block; width:300px; height:250px; background-color:#ffeb3b; border:1px solid #ddd;">
            <div style="padding:20px; text-align:center;">
                <h3>テスト広告 - AdSense</h3>
                <p>クリックしてテスト</p>
            </div>
        </ins>
    </div>
    
    <h2>2. iframe広告</h2>
    <div class="ad-container">
        <iframe id="test-ad-iframe" 
                name="google_ads_frame"
                src="data:text/html,<html><body style='margin:0;padding:20px;background:#e3f2fd;text-align:center;'><h3>iframe広告テスト</h3><a href='#' onclick='parent.postMessage(\"iframe-clicked\", \"*\");'>クリックテスト</a></body></html>"
                class="ad-iframe">
        </iframe>
    </div>
    
    <h2>3. 広告コンテナ (div)</h2>
    <div class="ad-container">
        <div id="google_ads_div_1" class="google-ad">
            <div class="ad-banner" onclick="alert('広告コンテナクリック!')">
                <h3>バナー広告テスト</h3>
                <p>コンテナ型広告のテスト</p>
            </div>
        </div>
    </div>
    
    <h2>4. GPT広告スロット</h2>
    <div class="ad-container">
        <div id="div-gpt-ad-test-300x250" style="width:300px; height:250px; background:#f3e5f5; border:1px solid #9c27b0; padding:20px; text-align:center;">
            <h3>GPT広告スロット</h3>
            <iframe src="data:text/html,<html><body style='margin:0;padding:20px;background:#fff3e0;text-align:center;'><h4>GPT iframe</h4><button onclick='alert(\"GPT広告クリック!\")'>クリック</button></body></html>"
                    style="width:100%; height:200px; border:none;">
            </iframe>
        </div>
    </div>
    
    <h2>5. 画像広告</h2>
    <div class="ad-container">
        <div id="banner_ad_container">
            <img src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='200'><rect width='300' height='200' fill='%23ff9800'/><text x='150' y='100' text-anchor='middle' fill='white' font-size='20'>画像広告テスト</text><text x='150' y='130' text-anchor='middle' fill='white' font-size='14'>クリックしてください</text></svg>" 
                 class="ad-image" 
                 alt="テスト広告" 
                 onclick="alert('画像広告クリック!')">
        </div>
    </div>
    
    <h2>6. リンク広告</h2>
    <div class="ad-container">
        <a href="#" onclick="alert('リンク広告クリック!'); return false;" class="ad-link">
            <div style="background:#4caf50; color:white; padding:15px; text-align:center; border-radius:5px;">
                <h3>リンク型広告</h3>
                <p>このリンクをクリック</p>
            </div>
        </a>
    </div>
    
    <h2>7. ボタン広告</h2>
    <div class="ad-container">
        <button class="btn" onclick="alert('ボタン広告クリック!')">
            📢 今すぐクリック - 特別オファー!
        </button>
    </div>
    
    <h2>8. script要素 (AdSense)</h2>
    <div class="ad-container">
        <script id="test-adsense-script" 
                src="data:text/javascript,console.log('AdSense script loaded');"
                data-ad-client="ca-pub-test">
        </script>
        <div>AdSenseスクリプト読み込み完了</div>
    </div>
    
    <div id="test-results" class="test-result">
        <h3>テスト結果:</h3>
        <div id="results-content">テスト実行待ち...</div>
    </div>
    
    <script>
        // メッセージリスナー（iframe用）
        window.addEventListener('message', function(event) {
            if (event.data === 'iframe-clicked') {
                alert('iframe内要素がクリックされました!');
            }
        });
        
        // ページ読み込み完了をログ
        window.addEventListener('load', function() {
            console.log('テストページ読み込み完了');
            document.getElementById('results-content').innerHTML = 'ページ読み込み完了 - テスト実行可能';
        });
    </script>
</body>
</html>
        """
        
        test_file_path = '/tmp/ad_test_page.html'
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return f'file://{test_file_path}'
    
    def detect_ads_on_test_page(self) -> List[Dict]:
        """テストページで広告要素を検出"""
        detected_ads = []
        
        try:
            logger.info("テストページでの広告検出を開始")
            
            # 1. ins.adsbygoogle要素
            ins_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ins.adsbygoogle')
            for idx, ins in enumerate(ins_elements):
                if ins.is_displayed():
                    detected_ads.append({
                        'element': ins,
                        'type': 'ins_adsbygoogle',
                        'selector': 'ins.adsbygoogle',
                        'description': f'AdSense ins要素 #{idx}',
                        'test_id': f'ins_{idx}'
                    })
                    logger.info(f"✓ AdSense ins要素を検出: #{idx}")
            
            # 2. iframe広告
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            for idx, iframe in enumerate(iframes):
                iframe_id = iframe.get_attribute('id') or ''
                iframe_name = iframe.get_attribute('name') or ''
                iframe_src = iframe.get_attribute('src') or ''
                
                is_ad_iframe = any([
                    'ad' in iframe_id.lower(),
                    'google' in iframe_name.lower(),
                    'test-ad' in iframe_id.lower()
                ])
                
                if is_ad_iframe and iframe.is_displayed():
                    detected_ads.append({
                        'element': iframe,
                        'type': 'iframe_ad',
                        'selector': f'iframe#{iframe_id}' if iframe_id else f'iframe[{idx}]',
                        'description': f'iframe広告: {iframe_id or iframe_name}',
                        'test_id': f'iframe_{idx}'
                    })
                    logger.info(f"✓ iframe広告を検出: {iframe_id or iframe_name}")
            
            # 3. 広告コンテナ
            containers = self.driver.find_elements(By.CSS_SELECTOR, 
                'div[id*="google_ads"], div[class*="google-ad"], div[id*="div-gpt-ad"]')
            
            for idx, container in enumerate(containers):
                if container.is_displayed():
                    container_id = container.get_attribute('id')
                    detected_ads.append({
                        'element': container,
                        'type': 'div_container',
                        'selector': f'div#{container_id}',
                        'description': f'広告コンテナ: {container_id}',
                        'test_id': f'container_{idx}'
                    })
                    logger.info(f"✓ 広告コンテナを検出: {container_id}")
            
            # 4. バナー広告 (クラス指定)
            banners = self.driver.find_elements(By.CSS_SELECTOR, 
                'div[id*="banner"], .ad-banner, .ad-image')
            
            for idx, banner in enumerate(banners):
                if banner.is_displayed():
                    detected_ads.append({
                        'element': banner,
                        'type': 'banner_ad',
                        'selector': f'banner[{idx}]',
                        'description': f'バナー広告 #{idx}',
                        'test_id': f'banner_{idx}'
                    })
                    logger.info(f"✓ バナー広告を検出: #{idx}")
            
            # 5. リンク広告
            ad_links = self.driver.find_elements(By.CSS_SELECTOR, '.ad-link, a[class*="ad"]')
            for idx, link in enumerate(ad_links):
                if link.is_displayed():
                    detected_ads.append({
                        'element': link,
                        'type': 'link_ad',
                        'selector': f'a.ad-link[{idx}]',
                        'description': f'リンク広告 #{idx}',
                        'test_id': f'link_{idx}'
                    })
                    logger.info(f"✓ リンク広告を検出: #{idx}")
            
            # 6. ボタン広告
            buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button.btn')
            for idx, button in enumerate(buttons):
                if button.is_displayed():
                    detected_ads.append({
                        'element': button,
                        'type': 'button_ad',
                        'selector': f'button.btn[{idx}]',
                        'description': f'ボタン広告 #{idx}',
                        'test_id': f'button_{idx}'
                    })
                    logger.info(f"✓ ボタン広告を検出: #{idx}")
            
            logger.info(f"テストページで合計 {len(detected_ads)} 個の広告要素を検出")
            return detected_ads
            
        except Exception as e:
            logger.error(f"広告検出エラー: {e}")
            return []
    
    def test_click_ad(self, ad_info: Dict) -> bool:
        """個別の広告要素をクリックテスト"""
        element = ad_info['element']
        ad_type = ad_info['type']
        description = ad_info['description']
        test_id = ad_info['test_id']
        
        logger.info(f"🎯 クリックテスト開始: {description} ({ad_type})")
        
        try:
            # 1. 要素までスクロールして待機
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(2)
            
            # 2. 要素の可視性と有効性を確保
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable(element))
            
            # 3. 要素が見えるかチェックと強制表示
            if not element.is_displayed():
                self.driver.execute_script("""
                    arguments[0].style.display = 'block';
                    arguments[0].style.visibility = 'visible';
                    arguments[0].style.opacity = '1';
                    arguments[0].style.pointerEvents = 'auto';
                """, element)
                time.sleep(1)
            
            click_success = False
            click_method_used = ""
            
            if ad_type == 'iframe_ad':
                # iframe広告の処理
                click_success, click_method_used = self._handle_iframe_click(element)
            else:
                # 通常要素の処理
                click_success, click_method_used = self._handle_normal_click(element)
            
            # 4. クリック後の処理
            time.sleep(1)
            
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
            
            # 成功の判定（アラートまたは新タブまたはクリック成功）
            actual_success = click_success or alert_detected or new_tab_opened
            
            # テスト結果を記録
            self.test_results.append({
                'test_id': test_id,
                'ad_type': ad_type,
                'description': description,
                'success': actual_success,
                'method': click_method_used,
                'alert_detected': alert_detected,
                'new_tab_opened': new_tab_opened,
                'timestamp': datetime.now().isoformat()
            })
            
            if actual_success:
                logger.info(f"✅ {description} - クリックテスト成功 ({click_method_used})")
            else:
                logger.warning(f"❌ {description} - クリックテスト失敗")
            
            return actual_success
                
        except Exception as e:
            logger.error(f"❌ クリックテストエラー ({description}): {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            # エラー時は失敗として記録
            self.test_results.append({
                'test_id': test_id,
                'ad_type': ad_type,
                'description': description,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            return False
    
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
    
    def run_full_test(self) -> Dict:
        """完全なテストスイートを実行"""
        start_time = datetime.now()
        logger.info("🚀 広告クリック機能テスト開始")
        
        try:
            # WebDriver起動
            self.driver = self.setup_driver()
            
            # テストページ作成・読み込み
            test_url = self.create_test_html()
            logger.info(f"📄 テストページ作成: {test_url}")
            
            self.driver.get(test_url)
            time.sleep(3)
            
            # ページタイトル確認
            page_title = self.driver.title
            logger.info(f"📖 ページタイトル: {page_title}")
            
            # 広告要素検出
            detected_ads = self.detect_ads_on_test_page()
            
            if not detected_ads:
                logger.warning("⚠️ テストページで広告要素が検出されませんでした")
                return {
                    'total_ads': 0,
                    'successful_clicks': 0,
                    'failed_clicks': 0,
                    'success_rate': 0,
                    'test_results': [],
                    'duration': (datetime.now() - start_time).total_seconds()
                }
            
            # 各広告要素をテスト
            successful_clicks = 0
            failed_clicks = 0
            
            for i, ad in enumerate(detected_ads):
                logger.info(f"📊 テスト進捗: {i+1}/{len(detected_ads)}")
                
                if self.test_click_ad(ad):
                    successful_clicks += 1
                else:
                    failed_clicks += 1
                
                # テスト間の待機
                time.sleep(random.uniform(1, 2))
            
            # 最終結果
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            success_rate = (successful_clicks / len(detected_ads) * 100) if detected_ads else 0
            
            results = {
                'total_ads': len(detected_ads),
                'successful_clicks': successful_clicks,
                'failed_clicks': failed_clicks,
                'success_rate': success_rate,
                'test_results': self.test_results,
                'duration': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            logger.info("="*60)
            logger.info("🎯 広告クリックテスト完了")
            logger.info(f"📊 検出した広告: {len(detected_ads)}個")
            logger.info(f"✅ 成功クリック: {successful_clicks}個")
            logger.info(f"❌ 失敗クリック: {failed_clicks}個")
            logger.info(f"📈 成功率: {success_rate:.1f}%")
            logger.info(f"⏱️ 実行時間: {duration:.1f}秒")
            logger.info("="*60)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {e}")
            return {
                'error': str(e),
                'total_ads': 0,
                'successful_clicks': 0,
                'failed_clicks': 0,
                'success_rate': 0,
                'test_results': [],
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """メイン実行関数"""
    print("🎯 広告クリック機能テストスクリプト")
    print("=" * 60)
    print()
    
    # テスター初期化
    tester = AdClickTester(headless=True)  # ヘッドレスモードでテスト
    
    try:
        # テスト実行
        results = tester.run_full_test()
        
        # 結果をファイルに保存
        import json
        with open('test_ad_click_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # サマリー表示
        print()
        print("📊 テスト結果サマリー:")
        print(f"   検出した広告: {results.get('total_ads', 0)}個")
        print(f"   成功クリック: {results.get('successful_clicks', 0)}個")
        print(f"   失敗クリック: {results.get('failed_clicks', 0)}個")
        print(f"   成功率: {results.get('success_rate', 0):.1f}%")
        print(f"   実行時間: {results.get('duration', 0):.1f}秒")
        print()
        
        # 詳細結果
        if 'test_results' in results:
            print("📋 詳細結果:")
            for result in results['test_results']:
                status = "✅" if result['success'] else "❌"
                print(f"   {status} {result['description']} ({result['ad_type']})")
        
        print()
        print("📁 詳細結果: test_ad_click_results.json")
        print("📝 実行ログ: test_ad_click.log")
        
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによって中断されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()