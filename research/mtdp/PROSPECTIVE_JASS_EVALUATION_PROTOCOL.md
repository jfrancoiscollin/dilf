# MTDP — protocole préenregistré pour une évaluation prospective indépendante de Jass (brouillon)

**Statut :** proposition méthodologique, **non exécutée** ; aucune performance mesurée ou cohorte admise. Propriétaire : relais fondation H43. Ne modifie pas les expériences ni les seuils de MTDP-D1.

## Question falsifiable
À budget de calcul égal, une politique Jass utilisant les caractéristiques spatiales MTDP choisit-elle des coups de regret inférieur à une politique Jass témoin, sur des positions jamais utilisées pour définir ou ajuster la politique ? La stabilité top-1/top-3 et le coût de calcul sont des résultats secondaires, pas des substituts à la qualité de décision.

## Séparation des données et gel préalable
1. **Avant tout calcul**, figer dans un manifeste versionné les SHAs de DILF, Jass, moteur arbitre, code d'échantillonnage, paramètres et seeds, ainsi que les identifiants des parties et la règle de déduplication des positions (FEN normalisée + joueur au trait).
2. Maintenir exclus de l'entraînement, du choix de seuils et de la validation D1 les tournois/événements réservés `fFgE7oED`, `P1RUlfJc`, `s7ahYqL4`, `D9PF2OSW` et leurs parties/FEN. Ce protocole ne les réaffecte pas à une cohorte prospective.
3. Sélectionner une cohorte **nouvelle**, indépendante des jeux utilisés pour construire les signatures et régler les hyperparamètres ; conserver la provenance des parties, les exclusions, les doublons et les erreurs de légalité. Ne jamais publier `score_blind=true` sans validation des champs imbriqués et d'un schéma fermé ; la résolution appartient à D1.
4. Geler **avant consultation des résultats** les critères d'admission, budgets, politique MTDP, politique témoin, arbitre, tests et conditions d'arrêt. Si un changement est requis, créer une nouvelle version du protocole et étiqueter la précédente comme exploratoire.

## Plan apparié
- Pour chaque position admise, exécuter les deux politiques sur le **même état**, avec la même limite de nœuds et, si applicable, plusieurs seeds préfixées. Randomiser l'ordre des politiques pour limiter les effets d'environnement.
- Rapporter les budgets historiques `10k/50k/200k` nœuds comme **strates de comparaison**, sans affirmer qu'ils sont optimaux. Enregistrer nœuds réellement visités, temps, profondeur et arrêts ; ne pas confondre budget nominal et coût réel.
- Obtenir une référence indépendante (analyse plus profonde et identique pour les deux coups candidats, ou arbitrage externe préspécifié). Si l'arbitre ne discrimine pas les coups, enregistrer une égalité/incertitude au lieu d'inventer un regret précis.

## Critères et analyses
**Critère principal :** différence appariée de regret `regret(MTDP) - regret(témoin)` dans l'unité native documentée de l'arbitre (négatif favorable à MTDP). Rapporter moyenne, médiane, distribution, intervalle de confiance par bootstrap **groupé par partie** (et non par position), effectif des parties/positions et valeurs manquantes. Ne pas présenter un résultat exploratoire comme significatif.

**Secondaires :** taux d'accord top-1, recouvrement top-3, stabilité entre seeds/profondeurs, nœuds et temps réellement consommés, taux d'égalité des coups et erreurs de légalité. Les résultats doivent être ventilés par budget et caractéristiques de position préspécifiées ; toute analyse a posteriori est explicitement exploratoire.

**Garde-fous :** audit des doublons entre groupes, séparation par partie et événement, vérification des coups légaux par moteur FMJD, absence de fuite de scores dans les entrées, empreintes SHA-256 des fichiers et sorties. Les échecs d'exécution ne sont jamais comptés comme décisions gagnantes.

## Décision et arrêt
- **Succès scientifique** seulement si l'intervalle de confiance du critère principal est entièrement favorable à MTDP **et** si la validité de l'arbitre, l'indépendance des données et les contrôles de provenance sont établis. Un seuil de taille d'effet minimale doit être fixé avant exécution, sans être choisi après observation.
- **Inconclusif** si l'intervalle inclut zéro, si les données sont insuffisantes ou si l'arbitre ne départage pas les coups.
- **Échec de validité / arrêt** en cas de fuite, collision entre cohortes, coups illégaux non résolus, absence d'artefacts, dépassement des ressources autorisées ou modification non préenregistrée. Ne pas extrapoler à la force en match sans tournoi prospectif dédié.

## Livrables attendus (non produits à ce stade)
Manifeste de préenregistrement ; cohorte et rapport de légalité/déduplication ; sorties par position et seed ; rapport statistique groupé par partie ; empreintes SHA-256 ; note de décision distinguant hypothèses, mesures et conclusions. **Aucune expérience, dépense, fusion ni déploiement n'est autorisé par ce document.**
