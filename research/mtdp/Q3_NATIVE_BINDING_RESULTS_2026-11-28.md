# Q3 — Liaison native du compteur, 28 novembre 2026

Protocole 964039909a65530d8f489f17055e8fc55bf627ef et plan adfc2af7… publiés avant appels. Standard initial unique, cinq paires AB/BA/AB/BA/AB, 10000 nœuds/appel, Jass cfe07fc sans patch, cible et recette existantes inchangées. Cache algorithmique froid (processus et TT neufs), cache OS non contrôlé. Aucun candidat, Scan, signature ou nouvelle campagne scientifique.

## Résultat local

**10/10 appels réussis, 100000 nœuds mesurés ; mêmes sorties sémantiques natives dans les deux bras et toutes répétitions.** Neuf coups légaux conservés, premier depth complet natif, compteur et enveloppe externe réconciliés. SHA-256 de la sortie sémantique commune : fdebb12648ede0d7785cdbb6bb4a2831c112d0227969002c2a79588ff8b2bd0f. Temps interne de Jass retenu séparément (microsecondes de recherche), toujours <= temps englobant. L’enveloppe externe inclut construction, setup, lancement/parsing, finish et audit du compteur ; la différence avec l’enveloppe du recorder n’est jamais soustraite.

| Paire locale | Plain (ms) | Instrumenté (ms) | Différence (ms) | Ratio |
|---|---:|---:|---:|---:|
|0|46,005989|45,154755|-0,851234|0,981497|
|1|9,741087|10,184727|0,443640|1,045543|
|2|9,195405|8,604154|-0,591251|0,935701|
|3|9,111578|36,662771|27,551193|4,023756|
|4|9,460295|9,600816|0,140521|1,014854|

Médiane des différences +0,140521 ms et médiane des ratios 1,014854 **descriptives uniquement**. Les différences changent de signe et une paire dépasse 4x : ne pas attribuer ce bruit au seul compteur, retrancher ce chiffre de futurs temps candidats, éliminer un outlier ou revendiquer une accélération. Cinq paires sur un seul plateau et une seule machine ne valident ni qualité égale ni effet causal précis. Toutes les mesures sont conservées, pas de minimum sélectionné ou d’échauffement ajouté.

## Vérification reproductible

`q3_native_binding.py` exécute le plan ; `q3_native_binding_evidence.py` relit hors ligne tous les stdout, nœuds, sémantiques, clocks et phases et recalcule le résumé. Les clocks ne sont pas des preuves d’authenticité d’exécution ; provenance binaire/source/compilateur et logs CI sont complémentaires. Échecs/timeout gardent brut et temps externe, nœuds inconnus restent null et le reçu complet est refusé. **110 tests locaux** passent, dont 14 nouveaux du binding/vérificateur en plus des 13 du compteur.

Bruts locaux complets, provenance et cinq paires : `validation/q3-native-local-2026-11-28.zip` ; vérification structurée `validation/q3-native-local-verification-2026-11-28.json`. Workflow dédié `.github/workflows/mtdp-q3-native-binding.yml` : une compilation native épinglée, tests, une seule reproduction distante de 10 appels selon le même plan, vérification hors ligne et artefact complet. Les temps et SHA des traces temporelles ne doivent pas être identiques entre machines ; comparer les invariants et sorties sémantiques, jamais réclamer un cmp des temps. **Reproduction distante à confirmer.**

## Prochaine décision Q3

Après reproduction distante, préparer le reçu de construction/setup au niveau d’un lot chaud et son amortissement sur toutes les cibles prévues, y compris échecs et fallback. Distinguer cache de représentation, TT et OS. L’instrumentation v1 reste froide et le benchmark scientifique reste bloqué tant qu’aucun candidat Q1/Q2 n’a franchi la validation indépendante. Si une mesure d’effet observateur plus précise est nécessaire, protocole technique séparé avec répétitions et contrôle du scheduling ; ne pas prolonger ou filtrer ces cinq paires après résultat. Pas de campagne stratégique redondante, élagage, nouveaux scores Scan, réservation ou gel. D1/Q2 conserve les abstractions relatives à l’action et l’admission fraîche ; Q1 H:43. PC de Jeff non requis pour cette vérification bornée.
