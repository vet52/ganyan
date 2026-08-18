import sqlite3
import time
import random
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

def tjk_veri_cek(tarih, hipodrom_adi, ilerleme_fonksiyonu=None):
    if ilerleme_fonksiyonu: ilerleme_fonksiyonu(10, "Hayalet Tarayıcı (Chrome) Başlatılıyor...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu") 
    chrome_options.add_argument("--disable-software-rasterizer") 
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    wait = WebDriverWait(driver, 15)
    
    try:
        yil, ay, gun = tarih.split("-")
        tjk_tarih_formati = f"{gun}/{ay}/{yil}"
        hedef_url = "https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisProgrami"
        
        if ilerleme_fonksiyonu: ilerleme_fonksiyonu(12, f"TJK Sunucularına Bağlanılıyor: {hipodrom_adi}...")
        driver.get(hedef_url)
        time.sleep(2) 
        
        driver.execute_script(f"document.getElementById('QueryParameter_Tarih').value = '{tjk_tarih_formati}';")
        driver.execute_script("$('#ajaxForm').submit();")
        time.sleep(4) 
        
        hipodrom_sekmesi = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{hipodrom_adi}')]")))
        driver.execute_script("arguments[0].click();", hipodrom_sekmesi)
        time.sleep(3) 
        
        kosu_tablolari = driver.find_elements(By.XPATH, "//table[.//td[contains(@class, 'AtAdi')]]")
        toplam_kosu = len(kosu_tablolari)
        
        if toplam_kosu == 0:
            if ilerleme_fonksiyonu: ilerleme_fonksiyonu(100, "HATA: Bu hipodromda koşu tablosu bulunamadı.")
            return

        baslangic_indeksi = max(0, toplam_kosu - 6)
        
        conn = sqlite3.connect("tjk_arastirma_merkezi.db")
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Yarislar WHERE yaris_id LIKE ?", (f"{tarih}_{hipodrom_adi}%",))
        cursor.execute("DELETE FROM Sonuclar WHERE yaris_id LIKE ?", (f"{tarih}_{hipodrom_adi}%",))
        
        # 🚨 YENİ: AGF Tablosu Hazırlığı
        cursor.execute("CREATE TABLE IF NOT EXISTS Gunluk_AGF (yaris_id TEXT, at_adi TEXT, agf REAL)")
        cursor.execute("DELETE FROM Gunluk_AGF WHERE yaris_id LIKE ?", (f"{tarih}_{hipodrom_adi}%",))
        conn.commit()
        
        toplanan_atlar_ve_linkler = []
        kayit_sayisi = 0
        
        toplam_hedef_kosu = toplam_kosu - baslangic_indeksi
        for islem_sirasi, kosu_indeks in enumerate(range(baslangic_indeksi, toplam_kosu)):
            gercek_kosu_no = kosu_indeks + 1
            yaris_id = f"{tarih}_{hipodrom_adi}_K{gercek_kosu_no}"
            
            if ilerleme_fonksiyonu: 
                yuzde = 15 + int((islem_sirasi / max(1, toplam_hedef_kosu)) * 10)
                ilerleme_fonksiyonu(yuzde, f"Faz 1: {islem_sirasi+1}. Ayak bülteni çekiliyor...")

            cursor.execute("INSERT OR IGNORE INTO Yarislar (yaris_id, tarih, hipodrom, pist, mesafe) VALUES (?, ?, ?, 'Kum', 1200)", (yaris_id, tarih, hipodrom_adi))
            
            guncel_tablo = driver.find_elements(By.XPATH, "//table[.//td[contains(@class, 'AtAdi')]]")[kosu_indeks]
            satir_sayisi = len(guncel_tablo.find_elements(By.XPATH, ".//tr[td[contains(@class, 'AtAdi')]]"))
            
            for satir_indeks in range(satir_sayisi):
                try:
                    satir = driver.find_elements(By.XPATH, "//table[.//td[contains(@class, 'AtAdi')]]")[kosu_indeks].find_elements(By.XPATH, ".//tr[td[contains(@class, 'AtAdi')]]")[satir_indeks]
                    at_hucresi = satir.find_element(By.XPATH, ".//td[contains(@class, 'AtAdi')]")
                    
                    try:
                        at_link_elementi = at_hucresi.find_element(By.TAG_NAME, "a")
                        at_adi = at_link_elementi.text.strip()
                        at_profil_linki = at_link_elementi.get_attribute("href") 
                    except:
                        at_adi = at_hucresi.text.strip().split('\n')[0].strip()
                        at_profil_linki = "Yok"
                    
                    if not at_adi: continue 
                    
                    hucreler = satir.find_elements(By.TAG_NAME, "td")
                    
                    b_kilo = 50.0
                    if len(hucreler) > 3:
                        kilo_text = hucreler[3].text.strip().replace(",", ".")
                        try: b_kilo = float(kilo_text) if kilo_text else 50.0
                        except ValueError: b_kilo = 50.0
                            
                    b_jokey = hucreler[4].text.strip() if len(hucreler) > 4 else "Bilinmiyor"
                    
                    b_hp = 0
                    if len(hucreler) > 7:
                        hp_text = hucreler[7].text.strip()
                        try: b_hp = int(hp_text) if hp_text else 0
                        except ValueError: b_hp = 0
                    
                    cursor.execute("""
                        INSERT INTO Sonuclar (yaris_id, at_adi, jokey, kilo, hp, hedef, at_profil_linki) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (yaris_id, at_adi, b_jokey, b_kilo, b_hp, random.choice([0, 0, 0, 0, 1]), at_profil_linki))
                    
                    if at_profil_linki != "Yok":
                        toplanan_atlar_ve_linkler.append({"at_adi": at_adi, "link": at_profil_linki, "yaris_id": yaris_id})
                        
                    kayit_sayisi += 1
                except Exception as e:
                    continue
                
        conn.commit()

        toplam_at = len(toplanan_atlar_ve_linkler)
        if ilerleme_fonksiyonu: ilerleme_fonksiyonu(25, f"Faz 2: Toplam {toplam_at} atın zeka havuzu oluşturuluyor...")

        for i, at in enumerate(toplanan_atlar_ve_linkler):
            if ilerleme_fonksiyonu:
                yuzde = 25 + int((i / max(1, toplam_at)) * 40)
                ilerleme_fonksiyonu(yuzde, f"Veri Avı: {at['at_adi']} geçmişi/idmanı inceleniyor ({i+1}/{toplam_at})...")

            try:
                driver.get(at['link'])
                bekleme_kisa = WebDriverWait(driver, 4)
                
                try:
                    gecmis_tablo_satirlari = bekleme_kisa.until(EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr")))
                    for gecmis_satir in gecmis_tablo_satirlari[:10]:
                        hucreler = gecmis_satir.find_elements(By.TAG_NAME, "td")
                        if len(hucreler) < 11: continue 
                        
                        g_tarih = hucreler[0].text.strip()
                        g_hipodrom = hucreler[1].text.strip()
                        g_pist = hucreler[2].text.strip()
                        g_mesafe = hucreler[3].text.strip()
                        g_derece = hucreler[4].text.strip()
                        
                        try: g_kilo = float(hucreler[5].text.strip().replace(",", "."))
                        except ValueError: g_kilo = 54.0
                            
                        g_jokey = hucreler[6].text.strip()
                        g_sure = hucreler[8].text.strip()
                        
                        try: g_hp = int(hucreler[11].text.strip())
                        except ValueError: g_hp = 40
                        
                        cursor.execute("""
                            INSERT INTO At_Gecmis_Performans (at_adi, kapanis_tarihi, hipodrom, pist_tipi, mesafe, jokey, kilo, hp, derece, sure)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (at['at_adi'], g_tarih, g_hipodrom, g_pist, g_mesafe, g_jokey, g_kilo, g_hp, g_derece, g_sure))
                except TimeoutException:
                    pass

                try:
                    idman_sekmesi = driver.find_element(By.XPATH, "//a[contains(text(), 'İdman') or contains(text(), 'Galop')]")
                    driver.execute_script("arguments[0].click();", idman_sekmesi)
                    time.sleep(1) 
                    
                    idman_satirlari = driver.find_elements(By.XPATH, "//div[contains(@id, 'idman') or contains(@id, 'Idman')]//table//tbody/tr")
                    
                    if not idman_satirlari:
                        idman_satirlari = driver.find_elements(By.XPATH, "//table[.//th[contains(text(), 'İdman')]]//tbody/tr")

                    for id_satir in idman_satirlari[:5]: 
                        i_hucreler = id_satir.find_elements(By.TAG_NAME, "td")
                        if len(i_hucreler) < 4: continue
                        
                        i_tarih = i_hucreler[0].text.strip()
                        i_sehir = i_hucreler[1].text.strip()
                        i_mesafe = i_hucreler[2].text.strip()
                        i_sure = i_hucreler[3].text.strip()
                        i_turu = i_hucreler[4].text.strip() if len(i_hucreler) > 4 else "Galop"
                        
                        cursor.execute("""
                            INSERT INTO At_Idman_Performans (at_adi, idman_tarihi, sehir, mesafe, sure, idman_turu)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (at['at_adi'], i_tarih, i_sehir, i_mesafe, i_sure, i_turu))
                except Exception:
                    pass
            except Exception as e:
                continue
                
        # 🚨 YENİ: FAZ 4 - AGF VE GANYAN KAZIMA MERKEZİ 🚨
        if ilerleme_fonksiyonu: ilerleme_fonksiyonu(66, "Faz 4: TJK AGF (Müşterek Bahis) Oranları Çekiliyor...")
        try:
            driver.get("https://www.tjk.org/TR/YarisSever/Info/Page/Agf")
            time.sleep(2)
            driver.execute_script(f"document.getElementById('QueryParameter_Tarih').value = '{tjk_tarih_formati}';")
            driver.execute_script("$('#ajaxForm').submit();")
            time.sleep(4)
            
            hipodrom_sekmesi_agf = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{hipodrom_adi}')]")))
            driver.execute_script("arguments[0].click();", hipodrom_sekmesi_agf)
            time.sleep(3)
            
            # Pandas ile AGF sayfasındaki tüm tabloları süpürür
            html_source = driver.page_source
            dfs = pd.read_html(html_source)
            
            for at_dict in toplanan_atlar_ve_linkler:
                at_adi_hedef = at_dict['at_adi']
                agf_degeri = 0.0
                
                for df in dfs:
                    for row in df.itertuples(index=False):
                        satir_metni = ' '.join(map(str, row))
                        if at_adi_hedef in satir_metni:
                            # Düzenli ifade ile "% 15.45" veya "%15,45" formatını yakalar
                            match = re.search(r'%\s*(\d+[,.]\d+)', satir_metni)
                            if match:
                                agf_degeri = float(match.group(1).replace(',', '.'))
                                break
                    if agf_degeri > 0: break
                
                if agf_degeri > 0:
                    cursor.execute("INSERT INTO Gunluk_AGF (yaris_id, at_adi, agf) VALUES (?, ?, ?)", (at_dict['yaris_id'], at_adi_hedef, agf_degeri))
                    
        except Exception as e:
            print(f"AGF Çekilemedi (Yarış sabahı henüz açıklanmamış olabilir): {e}")

        conn.commit()
        conn.close()
        if ilerleme_fonksiyonu: ilerleme_fonksiyonu(70, "TJK Web Kazıma (Scraping) işlemi başarıyla tamamlandı.")
    except Exception as e:
        if ilerleme_fonksiyonu: ilerleme_fonksiyonu(100, f"[-] Genel Hata: {e}")
    finally:
        driver.quit()
