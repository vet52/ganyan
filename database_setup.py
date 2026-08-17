import sqlite3

def veritabani_kur():
    conn = sqlite3.connect("tjk_arastirma_merkezi.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Yarislar (
            yaris_id TEXT PRIMARY KEY, tarih TEXT, hipodrom TEXT, pist TEXT, mesafe INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sonuclar (
            id INTEGER PRIMARY KEY AUTOINCREMENT, yaris_id TEXT, at_adi TEXT, jokey TEXT, 
            kilo REAL, hp INTEGER, hedef INTEGER, at_profil_linki TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS At_Gecmis_Performans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, at_adi TEXT, kapanis_tarihi TEXT, 
            hipodrom TEXT, pist_tipi TEXT, mesafe TEXT, jokey TEXT, kilo REAL, 
            hp INTEGER, derece TEXT, sure TEXT
        )
    """)
    
    # YENİ: İDMAN (GALOP) TABLOSU
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS At_Idman_Performans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, at_adi TEXT, idman_tarihi TEXT, 
            sehir TEXT, mesafe TEXT, sure TEXT, idman_turu TEXT
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    veritabani_kur()