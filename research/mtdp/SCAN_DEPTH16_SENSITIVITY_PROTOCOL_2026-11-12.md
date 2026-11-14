# MTDP — protocole préenregistré de sensibilité Scan profondeur 16 (2026-11-12)

## Question

Les conclusions des trois benchmarks Jass gelés (premier, réplication et initial-only) résistent-elles au passage du juge Scan 3.1 de profondeur 12 à profondeur 16 ? Ce contrôle **ne réentraîne pas** les signatures et ne relance pas Jass : il réévalue les mêmes actions déjà choisies.

## Gel et provenance

Utiliser exclusivement les trois manifestes déjà publiés :
- `research/mtdp/jass_benchmark/` (première cohorte, 28 cibles) ;
- `research/mtdp/jass_benchmark/replication-iPQl7g7q/` (75 cibles) ;
- `research/mtdp/jass_benchmark/initial-only-0gB7ETSW/` (17 cibles).

Avant toute exécution, enregistrer les SHA-256 des manifestes, des références profondeur 12, des résultats Jass, du binaire Scan et du fichier d'évaluation. Vérifier les chemins exacts et les fichiers réellement disponibles ; ne pas reconstruire un manifeste à partir des scores. Conserver les 120 cibles (28+75+17), sauf exclusions techniques documentées individuellement.

## Conditions constantes

Même binaire Scan 3.1 et fichier d'évaluation épinglés que dans les rapports de référence ; un thread, table de transposition froide par évaluation, sans livre ni tablebases. Seul le paramètre de profondeur change de 12 à 16. Évaluer **tous les successeurs légaux** de chaque position cible et de chaque source utilisée dans les transferts, plutôt que seulement les trois candidats, afin d'éviter une censure des optima. Ne modifier ni la liste des actions, ni les positions, ni les appariements. Documenter toute position dont la recherche ne termine pas ; ne pas la remplacer silencieusement.

## Critères et statistiques figés avant calcul

Pour chaque paire source/cible et chaque profondeur : ensemble des coups optimaux (égalités autorisées), disjonction des optima, couverture du meilleur coup cible par le premier et par les trois premiers coups source, regret en pions du premier et du meilleur des trois (optimum cible moins score du coup transféré). Pour chaque bras Jass et budget : regret du **coup déjà joué** par rapport au meilleur coup cible Scan à la profondeur correspondante ; différence appariée transfert moins témoin canonique et transfert moins natif. Ne jamais refaire les recherches Jass lors de cette analyse.

Publier par cohorte et globalement les effectifs, exclusions, changements de signe, médiane/moyenne, maxima, nombre de regrets ≥0,50, et la concordance profondeur 12/16. Regrouper l'incertitude par partie cible, avec bootstrap 10 000 répétitions et graine 20261112 ; distinguer les trois tournois et ne pas traiter 120 positions corrélées comme 120 parties indépendantes. Les trois cohortes sont sélectionnées, non aléatoires : ne pas généraliser au jeu entier.

## Critères d'arrêt et limites

Arrêter et documenter si les empreintes divergent, si la correspondance des coups est ambiguë, si le binaire/évaluation épinglés sont indisponibles, si un score manque ou si la profondeur 16 dépasse les ressources gratuites disponibles. Une profondeur supérieure n'est pas une vérité de tablebase. Ne pas qualifier un bras de meilleur sans amélioration robuste et préspécifiée ; l'absence de différence ne démontre pas l'équivalence.

## Livrables

1. Manifeste de provenance et empreintes SHA-256.
2. Références Scan profondeur 16 en JSON avec identifiants stables et sorties brutes nécessaires à l'audit.
3. Comparaison déterministe 12/16, tests de schéma et de correspondance des actions, rapport avec dénominateurs exacts.
4. Mise à jour du journal de relais indiquant commandes, runs, SHA et état confirmé/non exécuté.

**État au préenregistrement : aucun calcul profondeur 16 exécuté ni validation de ce document confirmée.**
