# ticketdive_bot_drission.py
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import random
from datetime import datetime, timedelta

# ==========================================
# ユーザー情報
# ==========================================
EMAIL = "m.hiroto114@gmail.com"
PASSWORD = "match114"
LAST_NAME = "あ"
FIRST_NAME = "あ"
PHONE_NUMBER = "07041890480"

# 起動タイミング
LOGIN_TIME_BEFORE_SALE = timedelta(seconds=60) 
# ==========================================

def wait_until(t):
    """指定時刻まで待機"""
    print(f"{t} まで待機します...")
    while datetime.now() < t:
        time.sleep(0.001)
    print("指定時刻になりました。")

def random_sleep(min_s, max_s):
    time.sleep(random.uniform(min_s, max_s))

def mimic_typing(ele, text):
    """
    人間風タイピング（ログイン用）
    DrissionPageの要素に対して1文字ずつ入力
    """
    # フォーカス
    ele.click()
    for ch in text:
        ele.input(ch)
        time.sleep(random.uniform(0.01, 0.05))

def launch_browser():
    """DrissionPageのブラウザ起動設定"""
    co = ChromiumOptions()
    
    # Macの場合、Chromeのパスを明示しないと動かないことがあるため、
    # 自動検出に任せるが、動かない場合はパス指定が必要。
    # co.set_paths(browser_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    
    # Bot検知回避の基本設定
    co.mute(True) # 音声をミュート
    
    # 毎回新しいプロファイルのような挙動にするため、特定フォルダを指定せず一時モードで動かす
    # (DrissionPageはデフォルトで既存のChromeが閉じていれば新規セッションで立ち上がる)
    
    page = ChromiumPage(co)
    return page

def main():
    print("==========================================")
    print("   TicketDive Bot - DrissionPage Ver.")
    print("==========================================")
    
    EVENT_URL = input("イベントURL: ").strip()
    
    while True:
        target_time_str = input("発売開始時刻 (HH:MM) : ").strip()
        try:
            parsed_time = datetime.strptime(target_time_str, "%H:%M")
            now = datetime.now()
            TARGET_TIME = now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            if TARGET_TIME < now:
                if input("過去の時間です。続行? (y/n): ").lower() != 'y': continue
            print(f"📅 設定日時: {TARGET_TIME}")
            break
        except ValueError:
            pass
            
    TICKET_TYPE = input("チケット種別 (例: 前方) : ").strip()
    TICKET_QUANTITY = input("枚数 (例: 1) : ").strip()

    while True:
        offset_input = input("リロード前倒し秒数 (例: 0.5) [Enterで0.5]: ").strip()
        if offset_input == "":
            RELOAD_OFFSET = timedelta(seconds=0.5)
            break
        try:
            RELOAD_OFFSET = timedelta(seconds=float(offset_input))
            break
        except ValueError:
            pass

    print("\n✅ 設定完了。待機モードに入ります...\n")

    # 1. 起動待機
    wait_until(TARGET_TIME - LOGIN_TIME_BEFORE_SALE)
    
    print("ブラウザ起動...")
    page = launch_browser()

    # -----------------------
    # ログイン処理
    # -----------------------
    print("ログインページへ移動...")
    page.get(EVENT_URL)
    
    # ログインボタンを探す（未ログインの場合）
    if page.ele('text:ログイン'):
        print("ログインを実行します。")
        page.ele('text:ログイン').click()
        
        # メール入力（人間風）
        if page.wait.ele_displayed('@name=email', timeout=10):
            print(f"メール入力: {EMAIL}")
            mimic_typing(page.ele('@name=email'), EMAIL)
        
        # パスワード入力（人間風）
        if page.ele('@name=password'):
            print("パスワード入力...")
            mimic_typing(page.ele('@name=password'), PASSWORD)
            
        # ログインボタン
        btn = page.ele('xpath://button[span[text()="ログインする"]]')
        if btn:
            btn.click()
            print("ログイン情報を送信。")
            page.wait.load_start() # 読み込み開始を待つ
            
        # 完了待ち
        time.sleep(2)
        page.get(EVENT_URL)
        print("✅ ログイン完了（または済み）")
    else:
        print("✅ 既にログイン済み、またはボタンが見つかりません。")

    # -----------------------
    # 発売直前待機
    # -----------------------
    wait_until(TARGET_TIME - RELOAD_OFFSET)

    print(f"🚀 リロード実行 ({datetime.now()})")
    page.refresh()
    
    # -----------------------
    # チケット選択
    # -----------------------
    # DrissionPageは wait.ele_displayed で要素出現を待てる
    # xpathで「チケット種別の文字が含まれるdivの中にあるselect」を探す
    xpath_select = f'xpath://div[contains(., "{TICKET_TYPE}")]//select'
    
    print("チケット選択肢を探索中...")
    if page.wait.ele_displayed(xpath_select, timeout=30):
        print(f"① 発見: {datetime.now()}")
        dropdown = page.ele(xpath_select)
        
        # DrissionPageのselectメソッドは強力（値でもテキストでも選べる）
        # ここでは値を指定
        dropdown.select(TICKET_QUANTITY)
        print(f"枚数選択: {TICKET_QUANTITY}")
    else:
        raise Exception("タイムアウト：チケット選択肢が見つかりませんでした")

    # -----------------------
    # 申し込みボタン
    # -----------------------
    # 「申し込みをする」ボタンを探す
    submit_btn_xpath = 'xpath://button[span[text()="申し込みをする"]]'
    
    # ボタンが押せるようになるまで連打トライ
    end_time = time.time() + 10
    clicked = False
    while time.time() < end_time:
        btn = page.ele(submit_btn_xpath)
        if btn:
            try:
                # 画面内になくてもDrissionPageはある程度押してくれるが
                # 念のためJSクリックは使わず、ネイティブに近いクリックを試行
                btn.click()
                clicked = True
                print(f"ボタンクリック: {datetime.now()}")
                break
            except:
                time.sleep(0.1)
        else:
            time.sleep(0.05)
            
    if not clicked:
        raise Exception("申し込みボタンが押せませんでした")

    # -----------------------
    # 最終確認・決済
    # -----------------------
    print("最終画面へ...")
    
    # コンビニ決済（最優先）
    konbini_xpath = 'xpath://span[text()="コンビニ決済（前払い）"]'
    if page.wait.ele_displayed(konbini_xpath, timeout=5):
        page.ele(konbini_xpath).click()
    else:
        print("決済ボタンが見つかりません（または遅延）")

    # お目当て（あれば）
    omeate_xpath = 'xpath://span[contains(text(), "お目当て")]/following-sibling::div/select'
    if page.ele(omeate_xpath):
        select_ele = page.ele(omeate_xpath)
        # 2番目のオプションを選ぶ（index指定はDrissionPageでは少し工夫がいるので、optionタグを直接探す）
        # selectタグの中の2番目のoptionをクリック
        options = select_ele.eles('tag:option')
        if len(options) > 1:
            options[1].click() # 0番目は「選択してください」の可能性が高いため1番目(2つ目)を選ぶ

    # 個人情報入力（DrissionPageなら高速入力でも検知されにくい）
    # .input() はクリアしてから入力してくれる
    if page.ele('@name=lastName'):
        page.ele('@name=lastName').input(LAST_NAME)
        page.ele('@name=firstName').input(FIRST_NAME)
        page.ele('@name=phoneNumber').input(PHONE_NUMBER)

    # 最終完了ボタン
    final_btn_xpath = 'xpath://button[span[text()="申し込みを完了する"]]'
    if page.wait.ele_displayed(final_btn_xpath, timeout=5):
        # 最後に一瞬だけ間を入れる（Bot検知の最終防壁対策）
        time.sleep(0.1)
        page.ele(final_btn_xpath).click()
        print(f"🔥 完了ボタンPUSH: {datetime.now()}")

    # 成功判定
    if page.wait.ele_displayed('text:申込完了', timeout=20):
        print("========================================")
        print(f"🏆 チケット取得成功: {datetime.now()}")
        print("========================================")
    else:
        print("完了画面が確認できませんでした。画面を確認してください。")

    # 終了せず維持
    input("Enterを押すと終了します...")
    # page.quit() 

if __name__ == "__main__":
    main()