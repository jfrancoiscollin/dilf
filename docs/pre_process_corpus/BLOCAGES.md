# Blocages cumulés — RÉSOLUS (mai 2026)

Tous les blocages identifiés pendant la production du manuel Débutant
ont été résolus par interpellation §4.11 + recherche exhaustive +
validation utilisateur.

## Récapitulatif

| Fixture | Coquille PDF | Résolution | Statut |
|---|---|---|---|
| BEG_CH09_007 (Dubois ch13 D5 p43) | `43-38` → `38-32` | R009 | ✅ Corrigé |
| BEG_CH10_008 (Dubois ch14 D6 p46) | `37-31 (26x28)` → `27-21 (17x28)` | R010 | ✅ Corrigé |
| BEG_CH13_004 (Dubois ch17 D4 p55) | `(18x27)` → `(27x18)` | R011 | ✅ Corrigé |

Voir `RESOLUTIONS_debutant.md` §R009, §R010, §R011 pour le détail de
chaque diagnostic et la méthode de validation.

## Patterns de coquilles observés

Les 3 coquilles forment ensemble une **typologie utile** pour le futur
détecteur automatique (suggestion §4 de `ameliorations_dilf_debutant.md`) :

1. **Substitution de coup** (R009) — un coup entier remplacé par un
   autre. Le plus dur à détecter automatiquement, nécessite une
   recherche exhaustive sur les coups blancs/noirs alternatifs.
2. **Inversion de chiffres** (R010) — décalage systématique sur
   plusieurs nombres (37↔27, 31↔21, 26↔17). Détectable par tests
   `±1` sur chaque digit.
3. **Inversion des opérandes** (R011) — `(aXb)` au lieu de `(bXa)`.
   Heuristique de premier recours : si `a` est vide, tester `(bXa)`.

Total : 3 coquilles sur 152 fixtures CORPUS = **2% de taux d'erreur** 
sur les solutions publiées (les positions, elles, sont correctes à
100% grâce au pipeline pixel-déterministe).
