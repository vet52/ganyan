def fayda_skoru(olasilik, ganyan, profil):
    if profil == "Güvenli (Favoriler)": 
        return olasilik
    elif profil == "Dengeli": 
        return olasilik * (ganyan ** 0.5)
    else: 
        return olasilik * ganyan # Sürpriz Arayan

def optimum_kupon(yaris_olasiliklari, max_butce, risk_profili, birim_fiyat=1.25):
    # 1. Başlangıç: Her ayaktan en iyi 1 atı al
    kupon = [[ayak[0]] for ayak in yaris_olasiliklari] 
    
    def maliyet_hesapla(k):
        carpim = 1
        for a in k: 
            carpim *= len(a)
        return carpim * birim_fiyat

    # --- 🚨 YENİ: BÜTÇEYE GÖRE ZORUNLU SİGORTA KURALI 🚨 ---
    # Yüksek bütçeli kuponlarda "Tek" (Banko) atılmasını yasaklıyoruz.
    min_at = 1
    if max_butce >= 5000:
        min_at = 3  # 5000 TL üstü kuponlarda her ayakta en az 3 at zorunlu
    elif max_butce >= 800:
        min_at = 2  # 800 TL üstü kuponlarda her ayakta en az 2 at zorunlu

    for i in range(6):
        while len(kupon[i]) < min_at and len(kupon[i]) < len(yaris_olasiliklari[i]):
            aday = yaris_olasiliklari[i][len(kupon[i])]
            gecici = [list(a) for a in kupon]
            gecici[i].append(aday)
            
            # Eğer minimum atı eklemek bütçeyi aşıyorsa dur (Matematiksel güvenlik)
            if maliyet_hesapla(gecici) <= max_butce:
                kupon[i].append(aday)
            else:
                break
    # -------------------------------------------------------------

    # --- 2. OPTİMİZASYON DÖNGÜSÜ (Dengeli Dağılım Algoritması) ---
    while True:
        maliyet = maliyet_hesapla(kupon)
        en_iyi_idx, en_iyi_fayda, eklenecek_at = -1, 0, None
        
        for i in range(6):
            if len(kupon[i]) < len(yaris_olasiliklari[i]):
                aday = yaris_olasiliklari[i][len(kupon[i])]
                gecici = [list(a) for a in kupon]
                gecici[i].append(aday)
                
                yeni_maliyet = maliyet_hesapla(gecici)
                maliyet_artisi = yeni_maliyet - maliyet
                
                if yeni_maliyet <= max_butce:
                    # 🚨 YENİ: YIĞILMA CEZASI 🚨
                    # Bir ayakta at sayısı arttıkça, o ayağa yeni at eklemenin cazibesini (faydasını)
                    # matematiksel olarak düşürüyoruz. Bu sayede sistem atları ayaklara homojen dağıtıyor.
                    denge_carpani = 1.0 / (len(kupon[i]) ** 1.2)
                    
                    # Fiyat performans oranını denge çarpanı ile törpülüyoruz
                    fayda = (fayda_skoru(aday['olasilik'], aday['ganyan'], risk_profili) / maliyet_artisi) * denge_carpani
                    
                    if fayda > en_iyi_fayda:
                        en_iyi_fayda, en_iyi_idx, eklenecek_at = fayda, i, aday
                        
        if en_iyi_idx == -1: 
            break
            
        kupon[en_iyi_idx].append(eklenecek_at)
        
    return kupon, maliyet_hesapla(kupon)