# D1-C — gate de provenance avant toute analyse décisionnelle

Statut : protocole pré-enregistré, **aucun corpus admis**. Ce document ne constitue ni une preuve d'indépendance ni une analyse de scores.

## Entrées obligatoires et chaîne de preuve

1. Épingler par SHA de commit/objet et SHA-256 le fichier source brut (parties, FEN ou archive) ; consigner URL, licence, date de collecte, méthode de décodage, version du parseur FMJD et nombre de parties.
2. Construire **avant toute lecture de scores Scan ou Jass** un inventaire de parties : identifiant de tournoi, identifiant de partie stable, hash du brut, hash de trajectoire normalisée, chaque FEN canonique avec trait et dames, numéro de demi-coup et hash canonique. Préserver l'ordre par partie.
3. Récupérer **indépendamment du candidat** le registre des quatre événements réservés (fFgE7oED, P1RUlfJc, s7ahYqL4, D9PF2OSW) et des cohortes historiques déjà évaluées. Pour chaque entrée conserver source, commit/artefact, SHA-256, règle d'alias, identifiants de partie et hashes brut/trajectoire/position. Ne jamais inférer la complétude d'un registre de listes vides.
4. Comparer avant découpage : alias tournoi/événement, identifiant de partie, hash brut, hash de trajectoire et hash de position. Une provenance inconnue ou une collision inexpliquée entraîne **quarantaine**, pas admission. L'audit `corpus_admission.py` est un contrôle structurel complémentaire : son champ `historical_exclusion_proven: false` est intentionnel et ne doit pas être requalifié en preuve.
5. Dédoublonner les parties par trajectoire normalisée ; identifier explicitement les FEN répétés entre parties (possibles transpositions) et empêcher leur présence dans des partitions différentes. Séparer entraînement, validation et test par tournoi/partie **avant** d'examiner les résultats moteur.
6. Geler manifestes, registre d'exclusion, paramètres de partition, exclusions et SHA-256 dans un reçu immuable. Faire relire le reçu par le relais de validation. Une cohorte précédemment scorée reste historique, même si son nom de fichier change.

## Critères de passage / arrêt

**PASS** uniquement si les six étapes sont traçables, le contrôle structurel est sans erreur, les quatre événements réservés sont exclus par identifiants et hashes, et la couverture du registre historique est authentifiée. **STOP** en cas de source manquante, alias ambigu, hash non reproductible, provenance contradictoire, fuite entre partitions, ou registre non authentifié. Une absence de collision avec un registre incomplet ne vaut pas preuve d'absence de fuite.

Après PASS seulement : calculer signatures L/LCB/enrichies sans scores cibles, puis top-1/top-3 et regret sur test par tournoi, avec bootstrap par partie. Ne jamais assimiler collision de signature, égalité des coups légaux, meilleur coup commun et équivalence minimax.

## Reçu attendu

`source_sha256`, `parser_commit`, `manifest_sha256`, `exclusion_registry_sha256`, `exclusion_registry_sources`, `reserved_event_coverage`, `historical_cohort_coverage`, `game_counts_by_split`, `quarantine_counts_by_reason`, `cross_split_duplicate_counts`, `audit_result`, `reviewer`, `decision`.

Aucun reçu de ce type n'est publié par le présent protocole.
