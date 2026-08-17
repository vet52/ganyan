from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier

def modeli_egit(X, y, model_tipi="XGBoost"):
    
    if "XGBoost" in model_tipi:
        # --- 🚀 XGBOOST (AGRESİF VE DETAYCI MOTOR) ---
        model = XGBClassifier(
            n_estimators=100,        
            max_depth=3,             
            learning_rate=0.03,      
            min_child_weight=5,      
            gamma=0.2,               
            subsample=0.8,           
            colsample_bytree=0.8,    
            random_state=42,         
            eval_metric='logloss',
            scale_pos_weight=2       
        )
    else:
        # --- 🌲 RANDOM FOREST (DENGELİ VE KONSENSÜS MOTORU) ---
        model = RandomForestClassifier(
            n_estimators=200,            # 200 farklı ağaç ortak karar alır
            max_depth=5,                 # Ağaç derinliği
            min_samples_split=10,        # Sürpriz ezberlemeyi önler
            min_samples_leaf=4,          # Uç yapraklardaki güvenilirlik payı
            class_weight='balanced',     # XGBoost'taki scale_pos_weight karşılığı
            random_state=42,
            n_jobs=-1                    # Bilgisayarın tüm işlemci çekirdeklerini kullanır (Hızlandırır)
        )
    
    # Seçilen motoru 14 Boyutlu Matris ile eğit
    model.fit(X, y)
    
    return model