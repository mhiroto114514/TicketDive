# ticketdive_bot_autologin.py
import time
import random
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException, 
    StaleElementReferenceException
)
from selenium.webdriver.common.action_chains import ActionChains

# ログイン情報（Botが毎回これを入力します）
EMAIL = "m.hiroto114@gmail.com"
PASSWORD = "match114"

# 申し込み情報
LAST_NAME = "あ"
FIRST_NAME = "あ"
PHONE_NUMBER = "07041890480"

# ログイン処理にかかる時間を考慮して、少し早めに起動する（例：発売2分前）
LOGIN_TIME_BEFORE_SALE = timedelta(seconds=60) 

# ==========================================

def pretty_sleep(a, b=None):
    if b is None:
        time.sleep(a)
    else:
        time.sleep(random.uniform(a, b))

def wait_until(t):
    print(f"{t} まで待機します...")
    now = datetime.now()
    sleep_seconds = (t - now).total_seconds() - 1
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
    while datetime.now() < t:
        time.sleep(0.001)
    print("指定時刻になりました。")

def human_like_typing(element, text, min_delay=0.03, max_delay=0.07):
    """人間らしくキー入力"""
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(min_delay, max_delay))

def human_like_typing_speedy(element, text):
    element.send_keys(text)

def human_move_and_click(driver, element):
    """人間らしい物理クリック（検知回避用）"""
    actions = ActionChains(driver)
    try:
        actions.move_to_element(element).pause(random.uniform(0.1, 0.2))
        actions.move_by_offset(random.uniform(-3, 3), random.uniform(-3, 3)).pause(random.uniform(0.1, 0.2))
        actions.click()
        actions.perform()
    except Exception:
        # ActionChains失敗時は標準クリック
        element.click()

def human_move_and_click_speedy(driver, element):
    actions = ActionChains(driver)
    try:
        actions.move_to_element(element).pause(random.uniform(0.03, 0.06))
        actions.click()
        actions.perform()
    except Exception:
        element.click()

def human_scroll_into_view(driver, element):
    """
    マウスホイールをコロコロ回して、対象が画面内に入ってくるまでスクロールする。
    JSによる強制スクロールではなく、物理的なホイール操作をシミュレートする。
    """
    try:
        # 要素のY座標を取得
        element_y = element.location['y']
        
        # 現在のスクロール位置を取得
        current_scroll_y = driver.execute_script("return window.scrollY;")
        
        # 画面の高さ
        viewport_height = driver.execute_script("return window.innerHeight;")
        
        # 要素が今の画面より下にあるか上にあるか判定
        # (要素の位置) - (現在のスクロール位置 + 画面の半分)
        delta_y = element_y - (current_scroll_y + (viewport_height / 2))
        
        # 距離があまりに近ければスクロールしない
        if abs(delta_y) < 100:
            return

        # ActionChainsのホイール操作を使う
        actions = ActionChains(driver)
        
        # 一気にスクロールせず、数回に分けてコロコロする（人間演出）
        steps = random.randint(2, 4) # 3〜6回に分割
        step_y = delta_y / steps
        
        for _ in range(steps):
            # scroll_by_amount は Selenium 4.2+ の機能
            # delta_x=0, delta_y=step_y
            actions.scroll_by_amount(0, int(step_y)).perform()
            
            # コロコロ...コロコロ...という間のゆらぎ
            time.sleep(random.uniform(0.05, 0.1))

        # 最後に念のため、要素がしっかり見える位置にあるか確認（微調整）
        # Bot検知に引っかからない安全なJSスクロールを保険として入れておく
        # (centerではなくnearestにすることで、画面内にあるなら動かないようにする)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'nearest'});", element)
        
    except Exception:
        # 万が一ホイール操作がコケたら、元のコードで保険をかける
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)


# Chrome（undetected）起動設定
def launch_driver():
    options = uc.ChromeOptions()
    # ★プロファイル指定なし（毎回新品のChrome）
    options.add_argument("--start-maximized")
    options.add_argument("--lang=ja-JP")
    options.page_load_strategy = 'eager'

    # Macフリーズ対策のため use_subprocess は使わない
    driver = uc.Chrome(options=options)
    time.sleep(3)
    driver.implicitly_wait(5)
    return driver

# メイン処理
def main():
    print("==========================================")
    print("      TicketDive Bot - Setup")
    print("==========================================")
    
    # 1. イベントURL入力
    EVENT_URL = input("イベントURLを入力してください: ").strip()
    
    # 2. 発売時刻入力（HH:MM形式） ★ここを変更しました
    while True:
        target_time_str = input("発売開始時刻 (HH:MM) : ").strip()
        try:
            # 入力された時間と分をパース
            parsed_time = datetime.strptime(target_time_str, "%H:%M")
            
            # 今日の日付と結合
            now = datetime.now()
            TARGET_TIME = now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            
            # 過去の時間だった場合の警告
            if TARGET_TIME < now:
                print(f"⚠️ 注意: 設定時刻 {TARGET_TIME} は過去の時間です。")
                confirm = input("それでも続行しますか？ (y/n): ").lower()
                if confirm != 'y':
                    continue
            
            print(f"📅 設定日時: {TARGET_TIME}")
            break
        except ValueError:
            print("⚠️ フォーマットが正しくありません。半角で 'HH:MM' (例: 22:00) の形式で入力してください。")
    
    # 3. チケット種別
    TICKET_TYPE = input("チケット種別 (例: 前方チケット) : ").strip()
    
    # 4. 枚数
    TICKET_QUANTITY = input("枚数 (例: 1) : ").strip()

    # 5. リロード時間 
    while True:
        offset_input = input("リロード前倒し秒数 (例: 0.5) [Enterで0.4]: ").strip()
        if offset_input == "":
            RELOAD_OFFSET = timedelta(seconds=0.4)
            print("👉 デフォルト値 (0.4秒) を設定しました。")
            break
        try:
            offset_val = float(offset_input)
            RELOAD_OFFSET = timedelta(seconds=offset_val)
            print(f"👉 リロード前倒しを {offset_val} 秒に設定しました。")
            break
        except ValueError:
            print("⚠️ 数値を入力してください。")
    
    print("\n✅ 設定完了。待機モードに入ります...\n")

    # 1. 起動時間を待つ
    login_start = TARGET_TIME - LOGIN_TIME_BEFORE_SALE
    wait_until(login_start)

    print("時間になりました。ブラウザを起動します（新品プロファイル）...")
    driver = launch_driver() 

    # 2. 自動ログイン処理
    print("ログインページへ移動して自動ログインを開始します。")
    # イベントページに行くと、未ログインならログインボタンが出るはず
    driver.get(EVENT_URL) 
    pretty_sleep(1.0, 2.0)

    try:
        # ログインリンクを探す
        print("ログインボタンを探しています...")
        login_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "ログイン"))
        )
        human_move_and_click(driver, login_link)
        
        # メール入力
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        pretty_sleep(0.1, 0.2)
        print(f"メールアドレス入力: {EMAIL}")
        email_el = driver.find_element(By.NAME, "email")
        human_like_typing(email_el, EMAIL)
        
        # パスワード入力
        pretty_sleep(0.1, 0.2)
        print("パスワード入力...")
        pw_el = driver.find_element(By.NAME, "password")
        human_like_typing(pw_el, PASSWORD)
        
        # ログインボタン押下
        pretty_sleep(0.1, 0.2)
        login_btn = driver.find_element(By.XPATH, '//button[span[text()="ログインする"]]')
        human_move_and_click(driver, login_btn)
        print("ログイン情報を送信しました。")
        
        # ログイン完了待ち（ページ遷移を確認）
        # ログイン後、イベントページに戻るかトップに行くかを待機
        pretty_sleep(1.0, 2.0)
        
        # 念のためイベントページへ再アクセス（確実にそのページにいる状態にする）
        driver.get(EVENT_URL)
        print("✅ 自動ログイン完了。イベントページで待機します。")

    except TimeoutException:
        print("⚠️ ログインリンクが見つかりませんでした。既にログイン済みの可能性があります。")

    # 3. 発売直前まで待機
    wait_until(TARGET_TIME - RELOAD_OFFSET)

    print("発売直前リロードを実行します。")
    driver.refresh()
    # ★重要：このrefreshではログアウトされません（同じブラウザセッション内だから）
    driver.implicitly_wait(0) 

    loop_start = time.perf_counter()
    while True:
        if time.perf_counter() - loop_start > 30:
            raise Exception("30秒超過しても要素検出できませんでした")
        try:
            ticket_dropdown = WebDriverWait(driver, 0.2).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    f"//div[contains(., '{TICKET_TYPE}')]//select[contains(@class, 'TicketTypeCard_numberSelector')]"
                ))
            )
            print(f"① リロード終了時刻: {datetime.now()} ★★★")

            break
        except TimeoutException:
            pretty_sleep(0.05, 0.1)
            driver.refresh()

    # 枚数選択         
    # 1. ドロップダウン（<select>タグ）自体をクリックして開く
    pretty_sleep(0.1, 0.2) 
    human_scroll_into_view(driver, ticket_dropdown)
    human_move_and_click(driver, ticket_dropdown)
    pretty_sleep(0.1, 0.2) # オプションが開くのを待つ

    # 2. 開いたリストから、目的のオプション（例: <option value="1">1</option>）を探す
    try:
        option_element = ticket_dropdown.find_element(By.XPATH, f".//option[@value='{TICKET_QUANTITY}']")
    except NoSuchElementException:
        print(f"エラー: ドロップダウン内に value='{TICKET_QUANTITY}' のオプションが見つかりません。")
        raise

        # 3. 見つけたオプションをクリックして選択する
    human_move_and_click(driver, option_element)
        
    print(f"チケット枚数「{TICKET_QUANTITY}」を選択しました。{datetime.now()}")

    # （前略）チケット枚数選択の後...
    
    # 申し込みボタンを探す（まずは要素の存在確認）
    submit_button_xpath = '//button[span[text()="申し込みをする"]]'
    submit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, submit_button_xpath))
    )
    
    pretty_sleep(0.3, 0.4)
    # ★★★ ここから修正：グルグル対策のリトライクリック ★★★
    print("申し込みボタンへのクリックを試行します（オーバーレイ待機中）...")
    
    # 最大10秒間、クリックが成功するまで粘る
    end_time = time.time() + 10
    click_success = False
    
    while time.time() < end_time:
        try:
            # 1. 毎回要素を取得し直す（DOMが書き換わっている可能性があるため）
            btn = driver.find_element(By.XPATH, submit_button_xpath)
            
            # 2. 邪魔なものがないかチェック（is_enabledだけじゃなく、クリック可能か）
            if btn.is_enabled() and btn.is_displayed():
                # 3. 人間らしくクリック
                human_scroll_into_view(driver, btn)
                
                # ここで「ElementClickInterceptedException」が出たらexceptに飛ぶ
                # つまり「グルグル」が被っていたらエラーになってリトライへ回る
                btn.click() 
                
                click_success = True
                print(f"申し込みボタンをクリックしました（成功）。{datetime.now()}")
                break # ループを抜ける
                
        except (ElementClickInterceptedException, StaleElementReferenceException):
            # グルグルに邪魔された(Intercepted) or 画面更新中(Stale)の場合
            print("グルグル待機中... 0.3秒後に再トライ")
            pretty_sleep(0.2, 0.4)
        except Exception as e:
            print(f"予期せぬエラー: {e}")
            break

    if not click_success:
        raise Exception("申し込みボタンが10秒経っても押せませんでした（グルグルが消えません）")

    # （後略）最終確認ページへ...

    # 最終確認ページに移動 → 各種入力（「お目当て」や決済選択など）
    # 1. まず「コンビニ決済」ボタンを探す（これがページ遷移の待機になる）
    print("最終確認ページへ遷移。支払い方法を探します...")
    try:
        konbini_radio = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[text()="コンビニ決済（前払い）"]'))
        )
        print(f"コンビニ決済ボタンを発見。(ページ遷移完了){datetime.now()}")
        current_time = datetime.now()
        elapsed_seconds = (current_time - TARGET_TIME).total_seconds()
        print(f"発売開始から経過時間: {elapsed_seconds:.2f}秒")

    except TimeoutException:
        print("エラー: コンビニ決済ボタンが10秒以内に見つかりませんでした。")
        raise # これは必須要素なのでエラーで止める

    # =====================
    # 5秒ルール分岐
    # =====================
    if elapsed_seconds > 6:
        # 5秒以上遅れている場合：なりふり構わず爆速モードへ
        print("⚡️⚡️⚡️ 5秒以上経過！緊急事態！【爆速モード】に切り替えます！ ⚡️⚡️⚡️")
        
        # 2. 次に「お目当て」選択（存在すれば。待機はごく短く）
        try:
            print("お目当てセレクタを探します...")
            omeate_dropdown = WebDriverWait(driver, 0.3).until( # ← 10秒から0.6秒に短縮
                EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "お目当て")]/following-sibling::div/select'))
            )

            # ドロップダウンをクリックして開く
            human_move_and_click_speedy(driver, omeate_dropdown)
            pretty_sleep(0.02, 0.04) # オプションが開くのを待つ

            # 2番目のオプション(index 1)を探す
            try:
                option_element = omeate_dropdown.find_element(By.XPATH, ".//option[2]")
            except NoSuchElementException:
                print(f"エラー: お目当てドロップダウンに2番目のオプションが見つかりません。")
                raise

            # 見つけたオプションをクリックして選択する
            human_move_and_click_speedy(driver, option_element)
            
            print(f"お目当てを選択しました。{datetime.now()}")
        except TimeoutException:
            print("お目当ては見つかりませんでした（スキップ）。") 

        # 3. 最後に「コンビニ決済」をクリック
        human_move_and_click_speedy(driver, konbini_radio)
        print(f"コンビニ決済を選択しました。{datetime.now()}")

        # コンビニ選択後にフォームが表示されるのを待つ
        pretty_sleep(0.1, 0.2)
        lastName_field = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.NAME, "lastName"))
        )
        human_like_typing_speedy(lastName_field, LAST_NAME)
        pretty_sleep(0.1, 0.2)
        human_like_typing_speedy(driver.find_element(By.NAME, "firstName"), FIRST_NAME)
        pretty_sleep(0.1, 0.2)
        human_like_typing_speedy(driver.find_element(By.NAME, "phoneNumber"), PHONE_NUMBER)
        print(f"氏名・電話番号を入力しました。{datetime.now()}")

        # 最終送信ボタン
        final_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[span[text()="申し込みを完了する"]]'))
        )
        human_move_and_click_speedy(driver, final_button)

        print(f"② 申し込みボタン押時刻: {datetime.now()} ★★★")

    else:
        # 5秒以内の場合：順調なので、検知されないよう人間モードを維持
        print("✅ タイムは順調です。BOT検知を避けるため【人間モード】で丁寧に進めます。")
        
        # 2. 次に「お目当て」選択（存在すれば。待機はごく短く）
        try:
            print("お目当てセレクタを探します...")
            omeate_dropdown = WebDriverWait(driver, 0.3).until( # ← 10秒から0.6秒に短縮
                EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "お目当て")]/following-sibling::div/select'))
            )

            # ドロップダウンをクリックして開く
            human_move_and_click(driver, omeate_dropdown)
            pretty_sleep(0.02, 0.04) # オプションが開くのを待つ

            # 2番目のオプション(index 1)を探す
            try:
                option_element = omeate_dropdown.find_element(By.XPATH, ".//option[2]")
            except NoSuchElementException:
                print(f"エラー: お目当てドロップダウンに2番目のオプションが見つかりません。")
                raise

            # 見つけたオプションをクリックして選択する
            human_move_and_click(driver, option_element)
            
            print(f"お目当てを選択しました。{datetime.now()}")
        except TimeoutException:
            print("お目当ては見つかりませんでした（スキップ）。") 

        # 3. 最後に「コンビニ決済」をクリック
        human_scroll_into_view(driver, konbini_radio)
        human_move_and_click(driver, konbini_radio)
        print(f"コンビニ決済を選択しました。{datetime.now()}")

        # コンビニ選択後にフォームが表示されるのを待つ
        pretty_sleep(0.2, 0.3)
        lastName_field = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.NAME, "lastName"))
        )
        human_like_typing(lastName_field, LAST_NAME)
        pretty_sleep(0.2, 0.3)
        human_like_typing(driver.find_element(By.NAME, "firstName"), FIRST_NAME)
        pretty_sleep(0.2, 0.3)
        human_like_typing(driver.find_element(By.NAME, "phoneNumber"), PHONE_NUMBER)
        print(f"氏名・電話番号を入力しました。{datetime.now()}")

        # 最終送信ボタン
        final_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[span[text()="申し込みを完了する"]]'))
        )
        human_scroll_into_view(driver, final_button)
        human_move_and_click(driver, final_button)

        print(f"② 申し込みボタン押時刻: {datetime.now()} ★★★")

    # 「申込完了」の文字が表示されるまで最大15秒待つ
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//span[text()="申込完了"]'))
    )

    # 現在時刻を取得して、分かりやすい形式で表示
    print("========================================")
    print(f"③ チケット取得成功時刻: {datetime.now()} ★★★")
    print("========================================")

    # 結果確認（例：完了メッセージの検出など）を待つ
    print("処理完了しました。ブラウザは30秒後に閉じます。")
    pretty_sleep(30)
    driver.quit()

if __name__ == "__main__":
    main()