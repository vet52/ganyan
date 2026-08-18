import sqlite3

def veritabani_kur():
    conn = sqlite3.connect("tjk_arastirma_merkezi.db")
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Yarislar (yaris_id TEXT PRIMARY KEY, tarih TEXT, hipodrom TEXT, pist TEXT, mesafe INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Sonuclar (yaris_id TEXT, at_adi TEXT, jokey TEXT, kilo REAL, hp INTEGER, hedef INTEGER, at_profil_linki TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS At_Gecmis_Performans (at_adi TEXT, kapanis_tarihi TEXT, hipodrom TEXT, pist_tipi TEXT, mesafe INTEGER, jokey TEXT, kilo REAL, hp INTEGER, derece TEXT, sure TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS At_Idman_Performans (at_adi TEXT, idman_tarihi TEXT, sehir TEXT, mesafe INTEGER, sure TEXT, idman_turu TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Ozet_At_Istatistik (at_adi TEXT, genel_kazanma_orani REAL, toplam_kosu INTEGER, son_3_derece_ort REAL, dinlenme_gunu INTEGER, ort_hiz REAL, max_hiz REAL, kum_kazanma REAL, cim_kazanma REAL, sentetik_kazanma REAL, son_1_ay_idman_sayisi INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Ozet_Jokey_Istatistik (jokey TEXT, jokey_kazanma_orani REAL, toplam_yaris INTEGER)''')
    
    # 🚨 YENİ: AGF tablosuna "ganyan" kolonu da eklendi ve her seferinde sıfırdan sorunsuz kuruluyor
    cursor.execute('''DROP TABLE IF EXISTS Gunluk_AGF''')
    cursor.execute('''CREATE TABLE Gunluk_AGF (yaris_id TEXT, at_adi TEXT, agf REAL, ganyan REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Kupon_Gecmisi (id INTEGER PRIMARY KEY AUTOINCREMENT, olusturulma_zamani TEXT, bulten_tarihi TEXT, hipodrom TEXT, maliyet REAL, risk_profili TEXT, kupon_detayi TEXT)''')
    
    conn.commit()
    conn.close()
