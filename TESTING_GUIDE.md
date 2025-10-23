# Guide de Test d'Extraction des URLs Détaillées

## 🎯 Objectif

Vérifier que le scraper collecte correctement le champ **`url_detail`** pour chaque consultation, permettant d'accéder facilement à la page détaillée et aux documents associés.

## 📋 Méthode de Test

### Option 1 : Test Rapide (Recommandé)

```powershell
# Test du scraper avec vérification automatique des URLs
python scripts\test_url_extraction.py
```

**Ce script va :**
- Extraire ~10 consultations du site PMMP
- Vérifier que chaque item a un `url_detail`
- Afficher les statistiques et exemples
- Ne PAS sauvegarder en base de données

**Résultat attendu :**
```
✅ EXCELLENT: Toutes les consultations ont une URL détaillée!
   Le champ url_detail sera correctement rempli dans la base.
```

---

### Option 2 : Test avec Analyse HTML

Si le test rapide échoue, analysez la structure du site :

```powershell
# 1. Extraire et sauvegarder une page HTML
python scripts\test_extraction_real.py

# 2. Analyser la structure pour trouver les bons sélecteurs
python scripts\analyze_html_structure.py logs\test_page_consultations.html
```

**Cette méthode :**
- Sauvegarde la page HTML dans `logs/`
- Analyse tous les tableaux et liens
- Propose les sélecteurs CSS corrects
- Génère du code Python

---

### Option 3 : Test Complet avec Scrapy

```powershell
# Test réel avec le spider Scrapy
cd scraper
scrapy crawl consultations_spider -a statut=en_cours -s CLOSESPIDER_ITEMCOUNT=5
```

**Vérifier dans les logs :**
```
✓ URL détail trouvée: https://www.marchespublics.gov.ma/...
```

---

## 🔧 Ajustement des Sélecteurs

Si les URLs ne sont pas capturées, modifier `scraper/selectors.py` :

```python
class ConsultationsSelectors:
    # Adapter selon la structure HTML réelle
    DETAIL_LINK = "a[href*='Details']"  # ← Modifier ici
    
    # Ou essayer:
    # DETAIL_LINK = "a.detail-link"
    # DETAIL_LINK = "td a:first-child"
    # DETAIL_LINK = "a[href*='consultation']"
```

**Workflow de débogage :**

1. **Analyser le HTML** :
   ```powershell
   python scripts\analyze_html_structure.py logs\test_page_consultations.html
   ```

2. **Identifier le sélecteur** dans la sortie :
   ```
   💡 [4] SÉLECTEURS CSS RECOMMANDÉS
   Pour les liens de détail:
     DETAIL_LINK = 'a[href*="detail"]'
   ```

3. **Mettre à jour** `scraper/selectors.py`

4. **Retester** :
   ```powershell
   python scripts\test_url_extraction.py
   ```

---

## ✅ Vérification du Champ url_detail

### Dans le Spider

Le spider utilise **3 stratégies** pour capturer l'URL :

```python
# 1. Sélecteur spécifique
detail_url = row.css(ConsultationsSelectors.DETAIL_LINK + '::attr(href)').get()

# 2. Premier lien de la ligne
if not detail_url:
    detail_url = row.css('a::attr(href)').get()

# 3. Lien contenant "detail" ou "consultation"
if not detail_url:
    all_links = row.css('a::attr(href)').getall()
    for link in all_links:
        if 'detail' in link.lower():
            detail_url = link
            break

# 4. Construction manuelle si rien n'est trouvé
if not detail_url and item['ref_consultation']:
    detail_url = f"{URL_BASE}?ref={item['ref_consultation']}"
```

### Dans la Base de Données

Après extraction et sauvegarde en DB :

```sql
-- Vérifier que toutes les consultations ont une URL
SELECT 
    COUNT(*) as total,
    COUNT(url_detail) as avec_url,
    COUNT(*) - COUNT(url_detail) as sans_url
FROM consultations;

-- Afficher quelques exemples
SELECT ref_consultation, titre, url_detail 
FROM consultations 
LIMIT 5;
```

---

## 📊 Exemples de Résultats Attendus

### Test réussi

```
✓ Item extrait avec URL:
  Ref: AO-2024-001
  Titre: Construction d'un centre de santé...
  URL: https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=AO-2024-001

📊 Statistiques:
  Total d'items extraits: 10
  Avec URL détaillée: 10 (100.0%)
  Sans URL détaillée: 0 (0.0%)

✅ EXCELLENT: Toutes les consultations ont une URL détaillée!
```

### Test avec problème

```
✗ Item SANS URL:
  Ref: AO-2024-002
  Titre: Fourniture de matériel informatique...

📊 Statistiques:
  Total d'items extraits: 10
  Avec URL détaillée: 3 (30.0%)
  Sans URL détaillée: 7 (70.0%)

⚠️ ATTENTION: Beaucoup d'items sans URL détaillée!
   Les sélecteurs doivent être ajustés.
```

---

## 🚀 Utilisation de l'URL en Production

Une fois que `url_detail` est correctement rempli :

### Via l'API

```bash
# Récupérer une consultation avec son URL
curl http://localhost:8000/api/v1/consultations/AO-2024-001

{
  "ref_consultation": "AO-2024-001",
  "titre": "Construction...",
  "url_detail": "https://www.marchespublics.gov.ma/...",
  ...
}
```

### En Python

```python
from database.connection import SessionLocal
from database.models import Consultation

db = SessionLocal()
consultation = db.query(Consultation).filter_by(
    ref_consultation="AO-2024-001"
).first()

print(f"URL de la page détaillée: {consultation.url_detail}")
# → Accéder aux documents DCE, avis, etc.
```

### Export CSV

L'URL est incluse dans les exports :

```powershell
python scripts\export_data.py
```

Fichier CSV généré :
```csv
Référence,Titre,Organisme,URL
AO-2024-001,Construction...,ONEE,https://www.marchespublics.gov.ma/...
```

---

## 🔍 Débogage Avancé

### Logs détaillés

```powershell
# Activer les logs DEBUG
$env:LOG_LEVEL="DEBUG"
python scripts\test_url_extraction.py
```

### Inspecter manuellement

1. Ouvrir le site dans le navigateur
2. Inspecter une ligne du tableau (F12)
3. Copier le sélecteur CSS
4. Tester dans la console :
   ```javascript
   document.querySelector('votre-selecteur')
   ```

### Capture d'écran

Le script `test_extraction_real.py` sauvegarde automatiquement :
- `logs/test_page_consultations.png` (capture d'écran)
- `logs/test_page_consultations.html` (HTML complet)

---

## ✅ Checklist Finale

- [ ] Test rapide réussi (`test_url_extraction.py`)
- [ ] 100% des items ont une `url_detail`
- [ ] Les URLs sont valides (commencent par `http://` ou `https://`)
- [ ] Les URLs sont absolues (pas relatives)
- [ ] Test en base de données (quelques insertions)
- [ ] Vérification via l'API
- [ ] Export CSV contient les URLs

---

## 📞 Support

En cas de problème :

1. Consulter `logs/scraper.log`
2. Vérifier la structure HTML avec `analyze_html_structure.py`
3. Tester manuellement les sélecteurs CSS
4. Ajuster `scraper/selectors.py`

**Note importante** : La structure du site PMMP peut changer. Ce guide permet de rapidement identifier et corriger les sélecteurs.
