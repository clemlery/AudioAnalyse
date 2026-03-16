# Refactors prioritaires

---

## 🔴 CRITIQUE — Bloquants pour le multi-utilisateur

### 1. USER_ID hardcodé — `constants/service.py:28`

Le `USER_ID` est une constante globale. Tout le pipeline (`process.py`, `reporting.py`, `visualize.py`) l'utilise implicitement. C'est le premier verrou à faire sauter : remplacer par un paramètre dynamique passé depuis la session Streamlit.

### 2. État global mutable — `process.py`

```python
last_track_played = None
last_date = None
current_loop_streak = 0
```

Ces variables module-level cassent dès qu'on traite deux utilisateurs en parallèle ou séquentiellement. À encapsuler dans un objet `IngestContext(user_id, ...)` passé en paramètre.

### 3. `reporting.py` et `visualize.py` sans `user_id`

Toutes les fonctions (`top_tracks`, `top_artists`, `artists_data_to_csv`, etc.) agrègent les données sans filtrer par utilisateur. Elles doivent toutes recevoir un `user_id` et filtrer les jointures sur `track_stream.user_id`.

### 4. Pipeline de données via CSV — `constants/service.py`

Les pages Streamlit lisent des CSVs statiques (`CSV_TRACK_PATH`, etc.). Ce modèle est incompatible avec plusieurs utilisateurs. Remplacer par des requêtes directes PostgreSQL filtrées par `user_id`.

---

## 🟡 IMPORTANT — Qualité et robustesse

### 5. Upload sans association utilisateur — `pages/4_import_data.py`

Le fichier est déposé dans `UPLOADS_PATH` sans savoir à quel utilisateur il appartient. Le callback OAuth doit créer/récupérer l'utilisateur en base, puis l'upload doit être tagué avec son `user_id`.

### 6. Pas de `user_id` dans le pipeline d'ingestion — `ingest.py`

`load_streaming_history_folder()` ne passe aucun contexte utilisateur à `exploit_streaming_history()`. Le `user_id` doit être un paramètre de toute la chaîne d'appel.

### 7. `BrowserTokenSource` avec IDs hardcodés — `factory.py`

```python
_SAMPLE_TRACK_ID  = "7BKLCZ1jbUBVqRi2FVlTVw"
_SAMPLE_ARTIST_ID = "6qqNVVTkY8uBg9cP3Jd7DAH"
```

Non bloquant mais fragile si Spotify modifie ses pages. Rendre ces IDs configurables via `constants/`.

### 8. Callback OAuth non géré — `auth.py` / `pages/4_import_data.py`

Le flux OAuth génère une URL mais le callback (`/callback`) n'est pas implémenté en Streamlit. Le code d'échange de token après redirection est absent. À implémenter proprement avec `st.query_params`.

---

## ⚪ MINEUR — Maintenance

### 9. Décorateurs de logging via métaclasse — `dao/base_dao.py`

Décorateurs appliqués sur toutes les méthodes statiques. Fonctionne mais peu idiomatique en Python moderne. Pas urgent.

### 10. Chemins de fichiers incohérents — `constants/service.py`

Utiliser `pathlib.Path` plutôt que `os.path` (déjà importé mais non utilisé de façon cohérente).

---

## 🔵 AJOUTS — Pour le nouvel objectif

### Infrastructure multi-utilisateur

**A. Session utilisateur dans Streamlit**
Système de session avec `st.session_state["user_id"]` persistant entre les pages. Chaque page vérifie si l'utilisateur est authentifié, sinon redirige vers la page d'import/login.

**B. Isolation des données par utilisateur**
Toutes les requêtes `TrackStream`, `TrackStreamDay` filtrées par `user_id`. Les métriques partagées (Artist, Track, Release, snapshots) restent communes — seules les tables de streaming sont per-user.

**C. Gestion de l'upload asynchrone**
L'ingestion JSON (Selenium + API Spotify) est longue. Il faut un worker background (ex : thread ou Celery/RQ simple) avec un statut visible dans l'UI (`st.progress`), sinon Streamlit timeout.

### Moteur de recommandations

**D. Nouvelles tables DB**
- `user_preference` : vecteur de préférences calculé (genres, artistes, tempo, énergie...)
- `recommendation` : cache des recommandations générées (`user_id`, `track_spotify_id`, `score`, `generated_at`, `reason`)
- `track_audio_features` : stocker les audio features Spotify (valence, energy, danceability, etc.)

**E. Récupération des audio features**
Nouveau `fetch_dao/audio_features_fetch_dao.py` pour appeler `/audio-features` sur les tracks ingérées. Ces features sont la base d'un filtrage par contenu.

**F. Algorithme de recommandation — 3 couches**
1. **Content-based** : cosine similarity sur les audio features + genres des artistes les plus écoutés
2. **Collaborative filtering** : utilisateurs avec profils d'écoute similaires (basé sur `track_stream` overlaps) → recommander ce qu'ils écoutent et pas l'utilisateur courant
3. **Popularity-weighted boost** : pénaliser les tracks très mainstream pour favoriser la découverte

**G. Page Streamlit de recommandations** — `pages/5_recommendations.py`
- Affiche les N tracks recommandées avec score et raison ("Parce que tu écoutes X", "Populaire chez les utilisateurs similaires")
- Feedback utilisateur (like/dislike) pour affiner le modèle
- Filtres : humeur (énergie haute/basse), genre, nouveauté

**H. Page analytics cross-utilisateurs (opt-in)**
- Trending tracks cette semaine sur la plateforme
- Comparaison de son profil avec la communauté
- "Vous êtes dans le top X% des fans de [genre]"

---

## 🗺️ Ordre d'implémentation suggéré

### Phase 1 — Multi-user (bloquant)

1. Supprimer `USER_ID` constant → paramètre dynamique
2. Encapsuler l'état global de `process.py`
3. Implémenter le callback OAuth + création User en DB
4. Filtrer `reporting.py` / `visualize.py` par `user_id`
5. Refactor UI pour session utilisateur

### Phase 2 — Recommandations

6. Fetch audio features → nouvelle table
7. Content-based recommendations
8. Page `5_recommendations.py`
9. Collaborative filtering (nécessite plusieurs users en base)