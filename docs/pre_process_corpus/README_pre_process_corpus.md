# pre_process_corpus/

Bagage de production des manuels pédagogiques Draught Master. Tout ce qui
est nécessaire pour reprendre où on en est ou démarrer un nouveau cycle
manuel est ici.

## Contenu

### Documents de cadrage et de référence (toujours à lire en premier)

| Fichier | Rôle |
|---|---|
| `CADRAGE_MANUELS.md` | Protocole maître de production (793 lignes). Décrit les 4 manuels, le format de fixture, le protocole anti-hallucination, le workflow conversation par conversation. |
| `ETAT_DILF.md` | État réel du framework dilf au démarrage. Liste les modules disponibles (game.py, notation/dubois.py, extract_diagrams.py) et le backlog restant. |
| `JOURNAL.md` | Trace chronologique de toutes les conversations manuels. Mis à jour à chaque fin de cycle. |

### Livrables du cycle Débutant (référence et archive)

| Fichier | Rôle |
|---|---|
| `manuel_debutant.md` | Manuel pédagogique prose, 16 chapitres, 841 lignes. |
| `fixtures_debutant.py` | 166 fixtures Python, 16 chapitres. Round-trip FEN 166/166 ✓. Validation moteur 135/135 OK. |
| `RESOLUTIONS_debutant.md` | 11 résolutions (R001-R011) consignées pendant la production. |
| `BLOCAGES.md` | Document de clôture — 3 blocages tous résolus (coquilles PDF Dubois). |
| `ameliorations_dilf_debutant.md` | Backlog initial des suggestions dilf (archive — l'état à jour est dans `ETAT_DILF.md`). |

### Outillage industriel réutilisable (à utiliser pour chaque nouveau manuel)

| Fichier | Rôle |
|---|---|
| `generate_chapter.py` | Générateur de fixtures depuis une définition déclarative `chN_def.py`. Supporte pions ET dames (dispatcher unifié PR #32). Portable via `DILF_ROOT`. |
| `validate_final_moves.py` | Validation moteur structurelle des `final_move`. Portable via `DILF_ROOT` + `FIXTURES_MODULE`. |

## Comment l'utiliser

### Au démarrage d'une conversation manuel (Intermédiaire / Avancé / Expert)

```
Phrase d'amorce :
"Lis le CADRAGE_MANUELS.md, le JOURNAL.md et l'ETAT_DILF.md, 
puis attaque le manuel <X>. Mode fonce autorisé."
```

Claude clone dilf, met `pre_process_corpus/` au PYTHONPATH, et utilise
`generate_chapter.py` + `validate_final_moves.py` pour produire le
manuel demandé.

### Localement (debug, validation manuelle)

```bash
# 1. Cloner dilf à côté ou définir DILF_ROOT
export DILF_ROOT=/chemin/vers/dilf

# 2. Lancer le pipeline d'extraction sur un PDF Dubois
cd $DILF_ROOT
python3 -m scripts.extract_diagrams render --pdf docs/corpus/<PDF>.pdf --pages <plage>
python3 -m scripts.extract_diagrams extract
python3 -m scripts.extract_diagrams materialize

# 3. Générer un chapitre depuis une définition
cd /chemin/vers/pre_process_corpus
python3 generate_chapter.py ch01_def.py > ch01_generated.py 2> ch01.log

# 4. Intégrer dans fixtures_<niveau>.py, puis valider
FIXTURES_MODULE=fixtures_intermediaire python3 validate_final_moves.py
```

## Conventions de nommage

- Fixtures : `BEG_CHnn_mmm` (Débutant), `INT_CHnn_mmm` (Intermédiaire),
  `ADV_CHnn_mmm` (Avancé), `EXP_CHnn_mmm` (Expert)
- Modules : `fixtures_<niveau>.py` doivent exposer une liste
  `ALL_<NIVEAU>_POSITIONS` consommée par `validate_final_moves.py`
- Wrapper : `BeginnerPosition`, `IntermediatePosition`, etc. — ou
  `PedagogicalPosition` si la suggestion §1 du backlog dilf est livrée

## Patterns de coquilles PDF connus (cycle Débutant)

Voir `CADRAGE_MANUELS.md` §4.13 et `ETAT_DILF.md` §3 pour la
typologie complète. Résumé :

1. **Substitution de coup** — heuristique : recherche exhaustive sur
   les coups blancs alternatifs.
2. **Inversion de chiffres** — heuristique : recherche exhaustive sur
   toute la séquence.
3. **Inversion des opérandes** — heuristique : si `(aXb)` invalide
   parce que `a` vide, tester `(bXa)`.

Statistique de référence : 4% de taux de coquilles sur les solutions
publiées par Dubois (positions, elles, correctes à 100% via pipeline
pixel-déterministe).

## PRs dilf de référence

- **PR #30** (mai 2026) : 4 détecteurs de motifs P3 (Napoleon,
  Manoury, Enfilade, Brûleur).
- **PR #31** (mai 2026) : `pedagogy/notation/dubois.py` — reconstruction
  des rafles de pion.
- **PR #32** (mai 2026) : extension dames — `enumerate_king_captures`,
  `reconstruct_king_capture`, dispatcher unifié `reconstruct_capture`.

Backlog restant (cf `ETAT_DILF.md` §6) : §1 (wrapper standardisé), §4
(détecteur coquilles), §5 (glossaire étendu `ad lib`/`+1p`), §6
(détecteurs de motifs pour les coups nommés), §7 (validation
interactive).
