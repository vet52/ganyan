import sqlite3
import pandas as pd
import numpy as np

def sureyi_saniyeye_cevir(sure_str):
    try:
        parcalar = str(sure_str).split('.')
        if len(parcalar) == 3:
            dakika = int(parcalar[0])
            saniye = int(parcalar[1])
            salise = int(parcalar[2])
            return (dakika * 60) + saniye + (salise / 100.0)
        return np.nan
    except:
        return np.nan

def verileri_hazirla():
    conn = sqlite3.connect("tjk_arastirma_merkezi.db")
    df_gecmis = pd.read_sql_query("SELECT * FROM At_Gecmis_Performans", conn)
    df_idman = pd.read_sql_query("SELECT * FROM At_Idman_Performans", conn)

    if df_gecmis.empty:
        conn.close()
        return None, None

    # --- 1. TEMEL VERİ TEMİZLİĞİ VE TİP DÖNÜŞÜMÜ ---
    df_gecmis['derece_num'] = pd.to_numeric(df_gecmis['derece'], errors='coerce').fillna(99)
    df_gecmis['hedef'] = (df_gecmis['derece_num'] == 1).astype(int)
    df_gecmis['mesafe'] = pd.to_numeric(df_gecmis['mesafe'], errors='coerce').fillna(1200)
    df_gecmis['kilo'] = pd.to_numeric(df_gecmis['kilo'], errors='coerce').fillna(56.0)
    df_gecmis['hp'] = pd.to_numeric(df_gecmis['hp'], errors='coerce').fillna(40)
    df_gecmis['tarih_obj'] = pd.to_datetime(df_gecmis['kapanis_tarihi'], format='%d/%m/%Y', errors='coerce', dayfirst=True)
    df_gecmis = df_gecmis.sort_values(by=['at_adi', 'tarih_obj'], ascending=[True, False])

    # --- BAĞIL ANALİZ (GRUP İÇİ KIYASLAMA) ---
    yaris_gruplari = df_gecmis.groupby('kapanis_tarihi') 
    df_gecmis['yaris_ort_kilo'] = yaris_gruplari['kilo'].transform('mean')
    df_gecmis['yaris_max_hp'] = yaris_gruplari['hp'].transform('max')
    
    df_gecmis['kilo_farki'] = df_gecmis['kilo'] - df_gecmis['yaris_ort_kilo']
    df_gecmis['hp_farki'] = df_gecmis['yaris_max_hp'] - df_gecmis['hp']

    # --- HIZ ENDEKSİ (SPEED RATING) HESAPLAMA ---
    df_gecmis['saniye'] = df_gecmis['sure'].apply(sureyi_saniyeye_cevir)
    df_gecmis['hiz_m_sn'] = np.where(df_gecmis['saniye'] > 0, df_gecmis['mesafe'] / df_gecmis['saniye'], 0)
    
    at_hiz = df_gecmis[df_gecmis['hiz_m_sn'] > 10].groupby('at_adi')['hiz_m_sn'].agg(['mean', 'max']).reset_index()
    at_hiz.columns = ['at_adi', 'ort_hiz', 'max_hiz']

    # --- PİST VE MESAFE UYUMU ZEKASI ---
    pist_uyumu = df_gecmis.groupby(['at_adi', 'pist_tipi'])['hedef'].mean().unstack(fill_value=0).reset_index()
    for kol in ['Kum', 'Çim', 'Sentetik']:
        if kol not in pist_uyumu.columns: pist_uyumu[kol] = 0.0
    pist_uyumu = pist_uyumu[['at_adi', 'Kum', 'Çim', 'Sentetik']]
    pist_uyumu.columns = ['at_adi', 'kum_kazanma', 'cim_kazanma', 'sentetik_kazanma']

    # --- FORM VE DİNLENME ---
    at_istatistik = df_gecmis.groupby('at_adi')['hedef'].agg(['mean', 'count']).reset_index()
    at_istatistik.columns = ['at_adi', 'genel_kazanma_orani', 'toplam_kosu']

    at_form = df_gecmis.groupby('at_adi').head(3).groupby('at_adi')['derece_num'].mean().reset_index()
    at_form.columns = ['at_adi', 'son_3_derece_ort']

    bugun = pd.Timestamp.today()
    at_son_yaris = df_gecmis.groupby('at_adi').first().reset_index()
    at_son_yaris['dinlenme_gunu'] = (bugun - at_son_yaris['tarih_obj']).dt.days.fillna(30)
    at_dinlenme = at_son_yaris[['at_adi', 'dinlenme_gunu']]

    # --- 🚨 YENİ: JOKEY ZEKASI (JOKEY BAŞARI ORANI) 🚨 ---
    jokey_istatistik = df_gecmis.groupby('jokey')['hedef'].agg(['mean', 'count']).reset_index()
    jokey_istatistik.columns = ['jokey', 'jokey_kazanma_orani', 'jokey_kosu_sayisi']

    # --- İDMAN (GALOP) ZEKASI ---
    if not df_idman.empty:
        df_idman['idman_tarihi_obj'] = pd.to_datetime(df_idman['idman_tarihi'], format='%d/%m/%Y', errors='coerce', dayfirst=True)
        son_30_gun_idmanlar = df_idman[(bugun - df_idman['idman_tarihi_obj']).dt.days <= 30]
        at_idman_sayisi = son_30_gun_idmanlar.groupby('at_adi').size().reset_index(name='son_1_ay_idman_sayisi')
    else:
        at_idman_sayisi = pd.DataFrame(columns=['at_adi', 'son_1_ay_idman_sayisi'])

    # --- TÜM ÖZELLİKLERİ BİRLEŞTİRME ---
    df_model = pd.merge(df_gecmis, at_istatistik, on='at_adi', how='left')
    df_model = pd.merge(df_model, at_form, on='at_adi', how='left')
    df_model = pd.merge(df_model, at_dinlenme, on='at_adi', how='left')
    df_model = pd.merge(df_model, at_hiz, on='at_adi', how='left')
    df_model = pd.merge(df_model, pist_uyumu, on='at_adi', how='left')
    df_model = pd.merge(df_model, at_idman_sayisi, on='at_adi', how='left')
    
    # JOKEY VERİSİNİ ANA TABLOYA EKLİYORUZ
    df_model = pd.merge(df_model, jokey_istatistik, on='jokey', how='left')
    
    df_model['son_1_ay_idman_sayisi'] = pd.to_numeric(df_model['son_1_ay_idman_sayisi'], errors='coerce').fillna(0.0)
    df_model['ort_hiz'] = pd.to_numeric(df_model['ort_hiz'], errors='coerce').fillna(15.0)
    df_model['max_hiz'] = pd.to_numeric(df_model['max_hiz'], errors='coerce').fillna(15.0)
    
    # Yeni çaylak jokeyler için varsayılan bir kazanma oranı belirliyoruz (Örn: %5)
    df_model['jokey_kazanma_orani'] = pd.to_numeric(df_model['jokey_kazanma_orani'], errors='coerce').fillna(0.05) 

    # --- YAPAY ZEKA GİRDİ MATRİSİ (ARTIK 14 BOYUTLU!) ---
    secilen_sutunlar = [
        'mesafe', 'genel_kazanma_orani', 'toplam_kosu', 
        'son_3_derece_ort', 'dinlenme_gunu', 
        'kilo_farki', 'hp_farki', 
        'ort_hiz', 'max_hiz', 'kum_kazanma', 'cim_kazanma', 'sentetik_kazanma',
        'son_1_ay_idman_sayisi', 'jokey_kazanma_orani'  # 🚨 14. PARAMETRE EKLENDİ 🚨
    ]
    
    X = df_model[secilen_sutunlar].fillna(0.0).astype(float)
    y = df_model['hedef'].astype(int)

    # --- ARAYÜZ İÇİN ÖZET ---
    ozet_tablo = pd.merge(at_istatistik, at_form, on='at_adi')
    ozet_tablo = pd.merge(ozet_tablo, at_dinlenme, on='at_adi')
    ozet_tablo = pd.merge(ozet_tablo, at_hiz, on='at_adi', how='left')
    ozet_tablo = pd.merge(ozet_tablo, pist_uyumu, on='at_adi', how='left')
    ozet_tablo = pd.merge(ozet_tablo, at_idman_sayisi, on='at_adi', how='left')
    
    ozet_tablo['son_1_ay_idman_sayisi'] = pd.to_numeric(ozet_tablo['son_1_ay_idman_sayisi'], errors='coerce').fillna(0.0)
    ozet_tablo['ort_hiz'] = pd.to_numeric(ozet_tablo['ort_hiz'], errors='coerce').fillna(15.0)
    ozet_tablo['max_hiz'] = pd.to_numeric(ozet_tablo['max_hiz'], errors='coerce').fillna(15.0)

    ozet_tablo.to_sql("Ozet_At_Istatistik", conn, if_exists="replace", index=False)
    
    # O gün binen jokeyin verisini hızlıca çekmek için yepyeni bir tablo oluşturuyoruz!
    jokey_istatistik.to_sql("Ozet_Jokey_Istatistik", conn, if_exists="replace", index=False)
    
    conn.close()
    
    return X, y