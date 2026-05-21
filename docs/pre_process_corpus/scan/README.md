# `scan/` — Analyses du moteur Scan

Ce dossier contient les analyses produites par le **moteur Scan**
(backend Draught Master), qui servent de **source de vérité tactique**
pour la rédaction des manuels.

## Pourquoi ce dossier existe

Le PRINCIPE DIRECTEUR du cadrage (`CADRAGE_MANUELS.md`) interdit à Claude
d'inventer la moindre combinaison ou le moindre verdict tactique. Or
Claude n'a pas accès à Scan dans une conversation. La solution :

1. L'utilisateur ou **Claude Code** lance Scan sur les positions d'un
   niveau.
2. Scan dépose ses analyses ici, dans `scan_analysis_<niveau>.json`.
3. Claude **lit** ce fichier et rédige le commentaire des manuels
   **à partir du PV** (variante principale) calculé par Scan — jamais
   d'une ligne qu'il aurait reconstruite lui-même.

## Format attendu : `scan_analysis_<niveau>.json`

Un objet JSON dont les clés sont les `id` de fixtures. Une entrée par
position :

```json
{
  "BEG_CH07_001": {
    "verified": true,
    "eval_start": -0.4,
    "best_move": "42-37",
    "pv": ["42-37", "25x34", "40x20", "15x24", "28-22", "17x28", "32x14"],
    "eval_after_pv": 1.8,
    "winning_for": "white",
    "scan_depth": 19,
    "notes": "La published_notation correspond au PV de Scan."
  }
}
```

### Champs

| Champ | Type | Description |
|-------|------|-------------|
| `verified` | bool | `true` si Scan a validé la position. Claude ne rédige de commentaire tactique **que si `true`**. |
| `eval_start` | float | Évaluation de la position de départ, en unités-pion (positif = avantage blanc). |
| `best_move` | str | Meilleur coup selon Scan, notation FMJD. |
| `pv` | list[str] | **Variante principale complète** (principal variation). C'est la ligne que Claude commente. |
| `eval_after_pv` | float | Évaluation à la fin du PV (pour qualifier le gain). |
| `winning_for` | str | `"white"`, `"black"` ou `"draw"`. |
| `scan_depth` | int | Profondeur d'analyse atteinte (traçabilité). |
| `notes` | str | Libre. **Doit signaler si `published_notation` diverge du PV** (= notation du livre corrompue). |

### Niveaux

- `scan_analysis_debutant.json` — manuel Débutant (préfixe `BEG_`)
- `scan_analysis_intermediaire.json` — à venir (préfixe `INT_`)
- `scan_analysis_avance.json` — à venir
- `scan_analysis_expert.json` — à venir

## Règle de divergence

Quand `published_notation ≠ pv` pour une fixture, **le PV Scan fait
foi**. La notation du livre est traitée comme suspecte (coquille ou
erreur de transcription PDF). La divergence doit être :

1. signalée dans le champ `notes` de l'analyse,
2. consignée dans `A_VERIFIER_MOTEUR.md`,
3. reflétée dans le commentaire du manuel (qui suit le PV, pas le livre).

Cas de référence : `BEG_CH07_002`, dont la `published_notation` est
incohérente (envoi à dame impossible, rafle finale impossible). Cf
`A_VERIFIER_MOTEUR.md` §1.
