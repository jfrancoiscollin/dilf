# À vérifier au moteur Scan — manuel Débutant

> **Fichier de suivi des items en attente de la phase de validation
> moteur** (cadrage §4.6 : transformation `verified=False → verified=True`).
>
> Cette phase nécessite le **backend Draught Master avec le moteur Scan**
> (non disponible dans une conversation Claude seule). Ce document
> rassemble tout ce qui attend ce passage, pour servir de checklist
> unique le jour où la validation moteur est lancée.
>
> Compagnon de `JOURNAL.md` (chronologique) et `BLOCAGES.md` (clôturé).

---

## Statut global

| Catégorie | Nombre | Bloquant pour publication ? |
|-----------|--------|------------------------------|
| Affirmations tactiques à élucider | 5 | Non (concepts, pas fixtures) |
| Fixtures `final_move=None` — rafles de dame | 18 | Non (limitation reconstruction) |
| Fixtures `final_move=None` — gambits | 3 | Non (comportement attendu) |
| Fixtures `final_move=None` — illustratives | 10 | Non (positions de règles) |
| **Validation « gagnant » de toutes les fixtures** | 135 + 31 | **Oui à terme** (cf §4.6) |

Aucun de ces items n'est bloquant pour un déploiement pédagogique du
manuel : les positions sont correctes (round-trip FEN 166/166), les
135 `final_move` reconstruits sont des rafles maximales légales
(validation structurelle FMJD passée). Ce qui manque est la validation
**« la combinaison est bien gagnante »**, qui nécessite l'évaluation
Scan en unités-pion.

---

## 1. Affirmations tactiques à élucider au moteur (5 cas)

Ces concepts mentionnent une « attaque X-Y » ou un mécanisme tactique
que la **géométrie de pion simple ne confirme pas** (cf
`position_facts.py`). Ce sont probablement des attaques post-sacrifice
ou des coups de dame légitimes, mais Claude **ne les a pas corrigés**
car la règle §4.7 du cadrage interdit de corriger ce qu'on ne comprend
pas. À trancher au moteur.

### BEG_CH07_003 — le plus suspect

- **Concept publié** : « Trait aux noirs. L'attaque 14-20 sur le pion
  blanc 25 ouvre un coup de dame à 49. »
- **Solution publiée** : `(14-20) 25x21 (16x49)`
- **Problème géométrique** : le coup noir `14-20` amène le pion en 20,
  adjacent au blanc 25 — mais la case derrière 25 (vue de 20) est
  **hors plateau** (25 est en case de bord droit). Le pion noir 20 ne
  peut donc pas capturer 25. Par ailleurs `25x21` (reprise blanche)
  ne s'explique pas par un simple saut de pion.
- **À élucider** : quel est le mécanisme exact ? S'agit-il d'un coup de
  dame (le 49 final suggère une promotion) ? La notation est-elle une
  coquille ?

### BEG_CH04_005

- **Concept** : « Le collage demande parfois d'éliminer un pion qui
  bloque la rafle finale avant de créer le point d'appui. »
- **Menaces réelles détectées** : pions en 22, 27.
- **À vérifier** : cohérence du mécanisme de collage décrit.

### BEG_CH04_008

- **Concept** : « Quand les noirs attaquent plusieurs pions
  simultanément, le collage est la défense canonique. »
- **Menaces réelles détectées** : pions en 26, 31.
- **À vérifier** : l'attaque multiple décrite.

### BEG_CH07_004

- **Concept** : « Partie historique 2013. L'attaque noire sur 3 pions
  laisse supposer un collage. »
- **Menaces réelles détectées** : pions en 26, 31.
- **À vérifier** : l'attaque sur 3 pions.

### BEG_CH07_011

- **Concept** : « Partie URSS 1965. Trait aux noirs. L'attaque noire
  sur 2 pions laisse supposer un collage gagnant. »
- **Menaces réelles détectées** : pions en 21, 27.
- **À vérifier** : l'attaque sur 2 pions et le caractère gagnant.

---

## 2. Fixtures `final_move=None` — rafles de dame (18 cas)

Ces combinaisons se terminent par une **rafle de dame** ou un envoi à
dame. Le `final_move` n'a pas été reconstruit automatiquement. La PR #32
de dilf (`enumerate_king_captures`, `reconstruct_king_capture`,
dispatcher unifié) devrait permettre d'en reconstruire une partie —
à relancer via `generate_chapter.py` avec le dispatcher unifié.

```
BEG_CH04_007  38-32 (27x49) 34-30 (49x24) 29x7
BEG_CH04_009  28-23 (19x48) 17-12 (48x19) 12x1
BEG_CH05_001  36-31 (26x46) 42-37 (46x39) 43x5
BEG_CH05_002  33-29 (24x33) 38x18 (13x22) 37-31 (26x48) 40-35 (48x30)
BEG_CH05_008  37-31 (26x48) 47-42 (48x22) 28x10
BEG_CH05_009  (13-19) 24x4 (11-16) 4x27 (21x45)
BEG_CH05_010  (14-19) 23x5 (4-10) 5x8 (3x45)
BEG_CH07_002  42-37 (19x28) 29-23 (28x19) 37-31 (26x37) 48-42 (37x48)
BEG_CH07_009  28-23 (26x48) 23x3 (48x30) 25x34
BEG_CH10_002  27-22 (18x27) 31x22 12-18 46-41 (18x27) 34-30 (25x34) ...
BEG_CH12_008  26-21 (17x28) 29-23 (18x29) 39-33 43x5
BEG_CH12_009  (15-20) 24x15 (4-10) 15x4 (18-22) 4x27 (21x45)
BEG_CH13_001  38-33 (29x49) 31-27 (49x24) 27x18
BEG_CH14_010  (14-20) 23x3 (17-21) 3x17 (21x34) 40x29 (24x11)
BEG_CH16_001  37-31 (26x48) 47-41 (48x33) 38x29
BEG_CH16_008  (14-19) 27x18 (13x22) 24x4 (17-21) 4x27 (21x23)
BEG_CH16_009  34x23 (19x48) 30x37 (48x31) 36x27
BEG_CH16_010  27-21 (16x29) 42-38 (23x43) 34x14 (25x34) 30x6
```

**Action** : relancer la reconstruction avec le dispatcher unifié
`reconstruct_capture` (PR #32), puis valider au moteur.

---

## 3. Fixtures `final_move=None` — gambits (3 cas)

Ces combinaisons se **terminent par un coup simple** (pas de rafle
finale). C'est le **comportement attendu** : un gambit n'a pas de rafle
maximale finale à reconstruire. Pas d'action requise, juste à confirmer
le caractère gagnant au moteur.

```
BEG_CH04_003  27-21 (16x18) 28-23
BEG_CH06_005  26-21 (27x16) 38-32
BEG_CH07_005  27-22 (18x27) 29-23
```

---

## 4. Fixtures `final_move=None` — illustratives (10 cas)

Positions des chapitres 1 et 2 (notation, règles du jeu). Ce sont des
**positions de démonstration** (déplacement, capture, promotion, règle
des 50 coups…), pas des combinaisons. Pas de `final_move` attendu. Pas
d'action requise.

```
BEG_CH01_001  (position initiale)
BEG_CH01_002  (après 32-28)
BEG_CH02_001  (déplacement pion 35)
BEG_CH02_002  (interdiction de recul, pion 22)
BEG_CH02_006  (prise obligatoire, pion 31)
BEG_CH02_008  (promotion, pion 6)
BEG_CH02_009  (déplacement de dame)
BEG_CH02_010  (capture de dame)
BEG_CH02_011  (non-soufflage)
BEG_CH02_012  (règle des 50 coups, dame contre dame)
```

---

## 5. Validation « gagnant » de l'ensemble (phase §4.6)

Au-delà des cas listés ci-dessus, le cadrage §4.6 prévoit que **toute**
fixture passe au moteur Scan pour confirmer que :

1. la position est légale (cohérence FMJD complète, prise maximale
   globale) ;
2. la `published_notation` / `final_move` est jouable ;
3. le verdict du moteur (évaluation en unités-pion) est cohérent avec
   l'`explanation` (la combinaison est bien gagnante pour le camp
   annoncé).

C'est ce passage qui transforme `verified=False → verified=True`.
**Aucune fixture du manuel Débutant n'a encore ce passage** (toutes à
`verified=False`). La validation structurelle déjà faite
(`validate_final_moves.py` : 135/135 rafles maximales légales) est un
pré-requis, pas un substitut.

---

## Procédure recommandée le jour de la validation moteur

1. Démarrer le backend Draught Master avec Scan disponible.
2. Reconstruire les 18 rafles de dame via le dispatcher unifié
   (`generate_chapter.py` + PR #32), réduire le nombre de
   `final_move=None`.
3. Élucider les 5 affirmations tactiques du §1 ci-dessus (passer chaque
   position à Scan, lire le PV, comparer au concept publié). Corriger
   les concepts si Scan révèle une incohérence ; sinon les valider.
4. Passer les 166 fixtures à `scan_engine.evaluate_pos()`, vérifier le
   caractère gagnant, basculer `verified=True`.
5. Mettre à jour `JOURNAL.md` avec le bilan, et clôturer ce fichier
   (ou le réduire aux items non résolus).
