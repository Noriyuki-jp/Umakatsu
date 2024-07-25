# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 08:35:48 2024

"""

# インポートするライブラリ
import tkinter as tk
import csv
import os
import datetime
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.select import Select
import numpy as np
from tkinter import messagebox as msgbox
from PIL import Image, ImageTk

#曜日
dow_lst = ["月", "火", "水", "木", "金", "土", "日"]
#JRA URL
pat_url = "https://www.ipat.jra.go.jp/index.cgi"
# レース会場のリスト
place_lst = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]

dataFolder = 'csv'
dataFile = 'data.csv'

window = tk.Tk()
window.geometry("430x650+500+200")
window.attributes("-topmost", True)
window.title("ウマ活")

iconfile = tk.PhotoImage(file="images/umakatsu.ico")
window.iconphoto(False, iconfile)

version='Ver.1.0.0-beta.1'

# 曜日を取得
def judge_day_of_week(date_nm):
    try:
        date_dt = datetime.datetime.strptime(str(date_nm), "%Y-%m-%d")
        # 曜日を数字で返す(月曜：1 〜 日曜：7)
        nm = date_dt.isoweekday()
        return dow_lst[nm - 1]
    except Exception as e:
        print(f'judge_day_of_week Exception : {e}')

# クリック処理
def click_css_selector(driver, selector, nm, wait_sec):
    try:
        el = driver.find_elements(By.CSS_SELECTOR, selector)[nm]
        driver.execute_script("arguments[0].click();", el)
        sleep(wait_sec)
    except Exception as e:
        print(f'click_css_selector Exception : {e}')
    
def scrape_balance(self, driver):
    try:
        return int(np.round(float(driver.find_element(By.CSS_SELECTOR, ".text-lg.text-right.ng-binding").text.replace(',', '').strip('円')) / 100))
    except Exception as e:
        print(f'scrape_balance Exception : {e}')

def check_and_write_balance(driver, date_joined):
    try:
        if not os.path.exists('log'):
            os.makedev('log')
            os.makedev('money')
        else:
            if not os.path.exists('money'):
                os.makedev('money')

        balance = scrape_balance(driver)
        deposit_txt_path = "log/money/deposit.txt"
        balance_csv_path = "log/money/" + date_joined[:4] + ".csv"
        if balance != 0:
            with open(deposit_txt_path, 'w', encoding='utf-8', newline='') as deposit_txt:
                deposit_txt.write(str(balance))
            with open(balance_csv_path, 'a', encoding='utf-8', newline='') as balance_csv:
                writer = csv.writer(balance_csv)
                writer.writerow([datetime.datetime.now().strftime("%Y%m%d%H%M"), str(balance)])
        return balance
    except Exception as e:
        print(f'check_and_write_balance Exception : {e}')

# ログイン
def login(inet_id, wait_sec, password_pat, kanyusha_no, pars_no, headlessFlg):
    
    try:
        success_flag = False
        
        options = Options()
        
        if headlessFlg == True:
            # ヘッドレスモード
            options.headless = True
        options.add_argument("--headless=new")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(pat_url)
        
        # 時間外確認
        offTime = False
        element = driver.find_element(By.XPATH, "/html/body/div[2]/span[1]")
        if element.text == 'ただいまの時間は投票受付時間外です。':
            msgbox.showinfo('メッセージ', 'ただいまの時間は投票受付時間外です。')
            offTime = True
        if offTime == True:
            success_flag = False
        else:
            # PAT購入画面に遷移・ログイン
            # INETIDを入力する
            driver.find_elements(By.CSS_SELECTOR, "input[name^='inetid']")[0].send_keys(inet_id)
            click_css_selector(driver, "a[onclick^='javascript']", 0)
            sleep(wait_sec)
            # 加入者番号，PATのパスワード，P-RAS番号を入力する
            driver.find_elements(By.CSS_SELECTOR, "input[name^='p']")[0].send_keys(password_pat)
            driver.find_elements(By.CSS_SELECTOR, "input[name^='i']")[2].send_keys(kanyusha_no)
            driver.find_elements(By.CSS_SELECTOR, "input[name^='r']")[1].send_keys(pars_no)
            click_css_selector(driver, "a[onclick^='JavaScript']", 0)
            # お知らせがある場合はOKを押す
            if "announce" in driver.current_url:
                click_css_selector(driver, "button[href^='#!/']", 0)
            success_flag = True
    except Exception as e:
        print(f"Login Failure:{e}")
        driver.close()
        driver.quit()
        success_flag = False
    return driver, success_flag

# 入金処理
def deposit(inet_id, wait_sec, password_pat, kanyusha_no, pars_no, deposit_money, headlessFlg):
    try:
        driver, success_flag = login(inet_id, wait_sec, password_pat, kanyusha_no, pars_no, headlessFlg)
        if success_flag == True:
            # 入出金ページに遷移する(新しいタブに遷移する)
            click_css_selector(driver, "button[ng-click^='vm.clickPayment()']", 0)
            driver.switch_to.window(driver.window_handles[1])
            # 入金指示を行う
            click_css_selector(driver, "a[onclick^='javascript'", 1)
            nyukin_amount_element = driver.find_elements(By.CSS_SELECTOR, "input[name^='NYUKIN']")[0]
            nyukin_amount_element.clear()
            nyukin_amount_element.send_keys(deposit_money)
            click_css_selector(driver, "a[onclick^='javascript'", 1)
            driver.find_elements(By.CSS_SELECTOR, "input[name^='PASS_WORD']")[0].send_keys(password_pat)
            click_css_selector(driver, "a[onclick^='javascript'", 1)
            # 確認事項を承諾する
            Alert(driver).accept()
            sleep(wait_sec)
            driver.close()
            driver.quit()
            print('deposit 終了')
        else:
            print("Deposit Failure")
    except Exception as e:
        print(f'deposit Exception : {e}')

# 馬券処理        
def buy(bet_list: list, date_nm, inet_id, wait_sec, password_pat, kanyusha_no, pars_no, deposit_money, ticket_nm, headlessFlg):
    driver, success_flag = login(inet_id, wait_sec, password_pat, kanyusha_no, pars_no, headlessFlg)
    date_joined = date_nm.strftime("%Y%m%d")
    fieldnames = ['bet_type', 'race_id', 'horse_number']
    if success_flag == True:
        # 購入処理開始
        # 通常投票を指定する
        click_css_selector(driver, "button[href^='#!/bet/basic']", 0)
        # logフォルダの中に一日ごとのログファイルを作る
        if not os.path.exists('log'):
            os.makedev('log')
        log_file_path = os.path.join("log", date_joined + ".csv")
        log_file_exist_flag = False
        if os.path.exists(log_file_path):
            log_file_exist_flag = True
            with open(log_file_path, encoding='utf-8', newline='') as csvfile:
                reader = csv.DictReader(csvfile, fieldnames = fieldnames)
                loaded_log = [row for row in reader]
        bet_log = []
        for bet_dict in bet_list:
            bet_exist_flag = False
            if log_file_exist_flag == True:
                for row in loaded_log:
                    if (bet_dict['bet_type'] == row['bet_type']) and (bet_dict['race_id'] == row['race_id']):
                        bet_exist_flag = True
                        break
            if (log_file_exist_flag == True) and (bet_exist_flag == True):
                print(bet_dict['race_id'], "Bet already exists")
                continue
            else:
                try:
                    place = place_lst[int(bet_dict['race_id'][4:6]) - 1]
                    dow = judge_day_of_week(date_nm)
                    lst = driver.find_elements(By.CSS_SELECTOR, "button[ng-click^='vm.selectCourse(oCourse.courseId)']")
                    for el in lst:
                        if (place in el.text) & (dow in el.text):
                            driver.execute_script("arguments[0].click();", el)
                            sleep(wait_sec)
                            break
                    # レース番号を指定する
                    race_nm = int(bet_dict['race_id'][10:12])
                    lst = driver.find_elements(By.CSS_SELECTOR, "button[ng-click^='vm.selectRace(oJgRn.nRaceIndex + 1)']")
                    for el in lst:
                        if str(race_nm) in el.text:
                            driver.execute_script("arguments[0].click();", el)
                            sleep(wait_sec)
                            break
                    if bet_dict['bet_type'] == 'umatan':
                        #馬単セレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_visible_text('馬単')
                        #方式セレクト
                        o_select_method = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectMethod']"))
                        o_select_method.select_by_visible_text('ボックス')
                    elif bet_dict['bet_type'] == 'umaren':
                        #馬連セレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_visible_text('馬連')
                        #方式セレクト
                        o_select_method = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectMethod']"))
                        o_select_method.select_by_visible_text('ボックス')
                    elif bet_dict['bet_type'] == 'wakuren':
                        #枠連セレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_visible_text('枠連')
                        #方式セレクト
                        o_select_method = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectMethod']"))
                        o_select_method.select_by_visible_text('ボックス')
                    elif bet_dict['bet_type'] == 'wide':
                        #ワイドセレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_visible_text('ワイド')
                        #方式セレクト
                        o_select_method = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectMethod']"))
                        o_select_method.select_by_visible_text('ボックス')
                    elif bet_dict['bet_type'] == 'sanrenpuku':
                        #三連複セレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_index(6)
                        #方式セレクト
                        o_select_method = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectMethod']"))
                        o_select_method.select_by_visible_text('ボックス')
                    elif bet_dict['bet_type'] == 'sanrentan':
                        #三連単セレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_index(7)
                        #方式セレクト
                        o_select_method = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectMethod']"))
                        o_select_method.select_by_visible_text('ボックス')
                    elif bet_dict['bet_type'] == 'tansho':
                        #単勝セレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_visible_text('単勝')
                    elif bet_dict['bet_type'] == 'fukusho':
                        #複勝セレクト
                        o_select_type = Select(driver.find_element(By.CSS_SELECTOR, "select[ng-model^='vm.oSelectType']"))
                        o_select_type.select_by_visible_text('複勝')
                    for horse_number in bet_dict['horse_number']:
                        # 購入する馬番をクリック
                        click_css_selector(driver, "label[for^=no{}]".format(horse_number), 0)
                        sleep(wait_sec)
                    # 購入金額を指定する
                    set_ticket_nm_element = driver.find_element(By.CSS_SELECTOR, "input[ng-model^='vm.nUnit']")
                    set_ticket_nm_element.clear()
                    set_ticket_nm_element.send_keys(ticket_nm)
                    # 購入用変数をセットする
                    click_css_selector(driver, "button[ng-click^='vm.onSet()']", 0)
                    click_css_selector(driver, "button[ng-click^='vm.onShowBetList()']", 0)
                    # 購入する
                    money = driver.find_element(By.CSS_SELECTOR, "span[ng-bind^='vm.getCalcTotalAmount() | number']").text
                    driver.find_element(By.CSS_SELECTOR, "input[ng-model^='vm.cAmountTotal']").send_keys(money)
                    click_css_selector(driver, "button[ng-click^='vm.clickPurchase()']", 0)
                    # 購入処理を完了させる
                    click_css_selector(driver, "button[ng-click^='vm.dismiss()']", 1)
                    #続けて投票するをクリック
                    driver.find_element(By.CSS_SELECTOR, "button[ng-click^='vm.clickContinue()']").click()
                except:
                    print(bet_dict['race_id'], "Bet failure")
                    continue
                sleep(wait_sec)
            if bet_exist_flag == False:
                bet_log.append(bet_dict)
            sleep(wait_sec)
        with open(log_file_path, 'a', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
            writer.writerows(bet_log)
        driver.close()
        driver.quit()
    else:
        print("Purchase Failure")

# 入金ボタン
def btn_Deposit():
    try:
        inet_id = entInet_id.get()
        kanyusha_no = entKanyusha_no.get()
        password_pat = entPassword_pat.get()
        pras_no = entPras_no.get() 
        deposit_money = entDeposit_money.get()
        ticket_nm = entTicket_nm.get()
        wait_sec = entWait.get()
        headlessFlg = hlessFlg.get()
        
        #入力チェック
        ret = chk_Data(inet_id, kanyusha_no, password_pat, pras_no, deposit_money, ticket_nm, wait_sec)
        
        if ret == True:
            deposit(inet_id, wait_sec, password_pat, kanyusha_no, pras_no, deposit_money, headlessFlg)
        
    except Exception as e:
        print(f'btn_Deposit Exception:{e}')
    
# 馬券データ取得
def readCSV():
    try:
        ret = False
        bet_list = []

        if not os.path.exists(dataFolder + "/" + dataFile):
            print('フォルダ無し')
        
        else:
            
            with open("csv\data.csv") as f:
                reader = csv.reader(f)

                for row in reader:
                    listData = []
                    dictData = {}
                    
                    listData = list(row)
                    dictData['bet_type'] = listData[0]
                    dictData['race_id'] = listData[1]
                    dictData['horse_number'] = listData[2:len(listData)]
                    
                    bet_list.append(dictData)
                    ret = True
        return ret, bet_list
        
    except Exception as e:
        print(f'readCSV Exception : {e}')
    
# 馬券購入ボタン
def btn_Buy():
    try:
        inet_id = entInet_id.get()
        kanyusha_no = entKanyusha_no.get()
        password_pat = entPassword_pat.get()
        pras_no = entPras_no.get() 
        deposit_money = entDeposit_money.get()
        ticket_nm = entTicket_nm.get()
        wait_sec = entWait.get()
        headlessFlg = hlessFlg.get()

        #入力チェック
        ret1 = chk_Data(inet_id, kanyusha_no, password_pat, pras_no, deposit_money, ticket_nm, wait_sec)
        
        if ret1 == True:
            # csvデータ取得
            ret2, bet_list = readCSV()
            
            if ret2 == False:
                msgbox.showinfo('メッセージ', '読み込むデータがありません。')
            else:
                date_nm = datetime.datetime.today().date()
                buy(bet_list, date_nm, inet_id, wait_sec, password_pat, kanyusha_no, pras_no, deposit_money, ticket_nm, headlessFlg)  

    except Exception as e:
        print(f'btn_buy Exception : {e}')

# 入力値チェック
def chk_Data(inet_id, kanyusha_no, password_pat, pras_no, deposit_money, ticket_nm, wait_sec):
    try:
        ret = False
        
        ret2 = msgbox.askyesno('確認', '処理を開始しますか？')
        
        if ret2 == True:
            if len(inet_id) == 0:
                msgbox.showinfo('メッセージ', 'INETIDが未入力です。')
                entInet_id.focus_set()
                
            elif len(kanyusha_no) == 0:
                msgbox.showinfo('メッセージ', '加入者番号が未入力です。')
                entKanyusha_no.focus_set()
            
            elif len(password_pat) == 0:
                msgbox.showinfo('メッセージ', 'PATのパスワードが未入力です。')
                entPassword_pat.focus_set()
                
            elif len(pras_no) == 0:
                msgbox.showinfo('メッセージ', 'P-RAS番号が未入力です。')
                entPras_no.focus_get()
                
            elif len(deposit_money) == 0:
                msgbox.showinfo('メッセージ', '入金金額が未入力です。')
                entDeposit_money.focus_get()
                
            elif len(ticket_nm) == 0:
                msgbox.showinfo('メッセージ', '購入枚数が未入力です。')
                entTicket_nm.focus_get()
                
            elif len(wait_sec) == 0:
                msgbox.showinfo('メッセージ', '待機時間が未入力です。')
                entWait.focus_get()
                
            else :
                ret = True
        
        else:
            msgbox.showinfo('メッセージ', '処理を中止します。') 
        
        return ret
        
    except Exception as e:
        print(f'chk_Data Exception:{e}')

# 馬券AIボタン
def btn_AI():
    msgbox.showinfo('メッセージ', '有料プランのみ利用可能です。')

# 閉じるボタン
def btn_Close():
    try:
        window.destroy()
        window.quit()
    except Exception as e:
        print(f'btn_Close Exception:{e}')
     
yJiku = 0
yJikuAdd = 30
xJiku1 = 10
xJiku2 = 100
xJiku3 = 250

# 画像（ヘッダ）
image_path1 = "images/umakatsu.png"
image1 = Image.open(image_path1)
tk_image1 = ImageTk.PhotoImage(image1)
label1 = tk.Label(window, image=tk_image1)
label1.place(x=xJiku1, y=10)

# INETID
yJiku+=(yJikuAdd*3)
tk.Label(window, text="INETID").place(x=xJiku1,y=yJiku)
entInet_id = tk.Entry(window)
entInet_id.place(x=xJiku2,y=yJiku)
entInet_id.insert(tk.END, '8KU4P5CB') #todo最終的には消す

# 閉じるボタン
btnClose = tk.Button(window, text="閉じる", command=btn_Close, width=18).place(x=xJiku3,y=yJiku)

# 加入者番号
yJiku+=yJikuAdd
tk.Label(window, text="加入者番号").place(x=xJiku1,y=yJiku)
entKanyusha_no = tk.Entry(window)
entKanyusha_no.place(x=xJiku2,y=yJiku)
entKanyusha_no.insert(tk.END, '65032367')

# 入金ボタン
tk.Button(window, text="入金", command=btn_Deposit, width=18).place(x=xJiku3,y=yJiku)

# PATのパスワード
yJiku+=yJikuAdd
tk.Label(window, text="PATのパスワード").place(x=xJiku1,y=yJiku)
entPassword_pat = tk.Entry(show='*')
entPassword_pat.place(x=xJiku2,y=yJiku)
entPassword_pat.insert(tk.END, '1210')

# 馬券購入ボタン
tk.Button(window, text="馬券購入", command=btn_Buy, width=18).place(x=xJiku3,y=yJiku)

# P-RAS番号
yJiku+=yJikuAdd
tk.Label(window, text="P-RAS番号").place(x=xJiku1,y=yJiku)
entPras_no = tk.Entry(window)
entPras_no.place(x=xJiku2,y=yJiku)
entPras_no.insert(tk.END, '2257')

# 競馬AI 実行ボタン
btnClose = tk.Button(window, text="競馬AI 実行", command=btn_AI, width=18, height=7, bg="sky blue").place(x=xJiku3,y=yJiku)

# JRA IPATへの入金金額[yen]
yJiku+=yJikuAdd
tk.Label(window, text="入金金額").place(x=xJiku1,y=yJiku)
entDeposit_money = tk.Entry(window)
entDeposit_money.place(x=xJiku2,y=yJiku)
entDeposit_money.insert(tk.END, '100')

# 馬券の購入枚数
yJiku+=yJikuAdd
tk.Label(window, text="購入枚数").place(x=xJiku1,y=yJiku)
entTicket_nm = tk.Entry(window)
entTicket_nm.place(x=xJiku2,y=yJiku)
entTicket_nm.insert(tk.END, '2')

# seleniumの待機時間[sec]
yJiku+=yJikuAdd
tk.Label(window, text="待機時間(秒)").place(x=xJiku1,y=yJiku)
entWait = tk.Entry(window)
entWait.place(x=xJiku2,y=yJiku)
entWait.insert(tk.END, '1')

# ヘッドレスモードチェックリスト
yJiku+=yJikuAdd
hlessFlg=tk.BooleanVar()
hlessFlg.set(True)
chkbtn = tk.Checkbutton(window, text="ヘッドレスモード", variable=hlessFlg).place(x=xJiku2,y=yJiku)

# 画像（フッター）
yJiku+=yJikuAdd
image_path2 = "images/bakenshi.png"
image2 = Image.open(image_path2)
tk_image2 = ImageTk.PhotoImage(image2)
label2 = tk.Label(window, image=tk_image2)
label2.place(x=xJiku1, y=yJiku)

# バージョン
yJiku+=(yJikuAdd*10)
tk.Label(window, text=version).place(x=xJiku1,y=yJiku)

window.mainloop()

