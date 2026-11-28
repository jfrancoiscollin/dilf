# Q3 — Setup et coût complet du lot chaud, 28 novembre 2026

Statut : **contrat d’instrumentation et contrôle synthétique**, pas cache stratégique Jass ni campagne d’efficacité. Suite du reçu natif froid validé à 323f464 ; PR43 ouverte/draft, neuf contrôles success, aucun équivalent actif/en attente. Cadre Q1/Q2/Q3 et responsabilités déjà consignés : aucun nouveau candidat Q1/Q2 indépendamment validé, donc aucune campagne de recherche, signature, scoring ou sélectivité.

## Contrat disponible

Nouvelle entrée opt-in `q3_warm_batch.WarmBatchRecorder` et audit hors ligne, séparés des compteurs froids et méthodes gelées. Le cache décrit est un **cache de représentation** ; TT réutilisée et cache OS contrôlé sont refusés par cette version. Cela ne certifie pas un état OS froid. Identité du cache par SHA-256 et plan ordonné de toutes les requêtes obligatoires.

- Construction/chargement mesurés une fois, avant les requêtes ; omettre le setup est une erreur. Le temps précédant la première requête, y compris les trous de chronométrage, reste facturé au setup.
- Enveloppes de requêtes disjointes, phases setup/signature/lookup/vérification/fallback/recherche exclusives ; leur orchestration et les intervalles entre requêtes restent dans le total.
- `temps du lot = setup complet + enveloppes des requêtes + orchestration entre/après requêtes`.
- Amortissements exacts sous forme numérateur/denominateur : setup/N_prévu et total/N_prévu. **N_prévu inclut hit, miss, bypass, fallback, erreurs, timeout et emplacements non exécutés**. Les doublons, omissions ou réordonnancements sont refusés. Un emplacement non exécuté doit être explicite, sans travail inventé.
- Coût par emplacement prévu n’est pas débit par succès : une requête manquante/échouée rend `all_planned_succeeded` faux ; une méthode qui échoue tôt ne devient pas un succès à qualité égale parce qu’elle paraît moins chère. Conserver également tentatives, réussites, fallback, erreurs et couverture.
- Nœuds réels de setup et de requêtes tous comptés ; setup et limites individuelles sont alloués avant exécution et leur somme doit égaler le plafond du lot. Un surplus global ne masque pas le dépassement d’un appel ou d’une requête. La cohérence de plafonds n’est pas une mesure d’égalité de qualité.
- Nœuds inconnus lors d’un échec restent null, avec somme partielle connue séparée ; total complet et conformité budgétaire non établis. Jamais zéro substitué. Un succès avec télémétrie inconnue est refusé.
- Octets du payload du cache conservés distinctement ; ils ne mesurent ni RSS/peak mémoire, ni taille réelle du codec avec clés/dictionnaires/modèle, ni compression décisionnelle.

Le recorder utilise une horloge monotone. Son audit expose l’amortissement de l’enveloppe interne et le marque explicitement comme excluant sa propre construction/finalisation. **Le coût primaire par emplacement est l’enveloppe externe/N_prévu**, et non cet amortissement interne ; le contrôle conserve ce numérateur et ce dénominateur séparément. Comme pour le témoin natif, une enveloppe externe de contrôle inclut sa construction/finalisation et son audit, sans soustraction de surcoût. Compilation, authentification préalable et sérialisation/archivage des preuves sont hors chronométrage du travail contrôlé. Le validateur vérifie la cohérence des mesures déclarées, pas l’authenticité d’un processus ni une économie de calcul.

## Contrôle et métrique vérifiés localement

`q3_warm_batch_smoke` construit un dictionnaire Python d’un octet sous une clé **explicitement synthétique**, sans position, signature, R2, Jass ou Scan. Deux scénarios fixés de trois emplacements chacun :

| Scénario | Prévus | Tentés | Hit réussi | Fallback après miss | Erreur simulée | Timeout simulé | Non exécuté |
|---|---:|---:|---:|---:|---:|---:|---:|
| Plan parcouru | 3 | 3 | 1 | 1 | 1 | 0 | 0 |
| Plan interrompu | 3 | 2 | 1 | 0 | 0 | 1 | 1 |

Le dénominateur reste **3 dans les deux scénarios**, setup mesuré et facturé une seule fois, zéro appel moteur et zéro nœud moteur réel. Les échecs sont délibérément simulés, pas incidents CI. Les enveloppes brutes et les audits sont relus hors ligne ; les deux lots sont impropres à une comparaison de qualité puisqu’ils comportent des échecs intentionnels. Aucun gain de temps, qualité, force ou mémoire n’est revendiqué.

**126 tests locaux passent**, dont 16 nouveaux sur le lot chaud : dénominateur, coûts de setup/échec/fallback, non-exécution, nœuds inconnus, plafonds individuels, chevauchements, payload et confusion TT/OS. Les fixtures unitaires à nœuds fictifs ne sont pas des reçus d’exécution moteur. Les tests à horloge réelle n’appellent aucun moteur.

Reproduction :

```bash
python -m pytest -q research/mtdp/tests/test_q3_warm_batch.py research/mtdp/tests/test_q3_cost_receipt.py research/mtdp/tests/test_q3_native_binding.py research/mtdp/tests/test_q3_native_binding_evidence.py research/mtdp/tests/test_metered_engine_smoke.py research/mtdp/tests/test_total_budget.py
python -m research.mtdp.jass_benchmark.q3_warm_batch_smoke --output-dir /tmp/q3-warm-example
```

Résumé sémantique versionné `validation/q3-warm-batch-contract-2026-11-28.json` ; traces locales complètes et résumé dans `validation/q3-warm-batch-local-2026-11-28.zip`. La CI dédiée doit reproduire le résumé logique, pas les horloges variables entre machines. **Validation distante à confirmer.** Les API froides, sources/patches/recettes Jass et anciens résultats restent inchangés.

## Décision suivante

Le contrat de setup/amortissement est prêt pour une intégration **après** réception d’un paquet candidat Q1/Q2 : définition/hash de cache et action-map, preuve indépendante de qualité/regret/WDL, provenance/licence, exclusions/partitions authentifiées, fallback et protocole de budgets. Ne pas inventer ce candidat, réutiliser le holdout connu ou empiler des profils synthétiques pour prétendre progresser sur la force. L’intégration chaude réelle, le codec/mémoire complet et la comparaison à qualité égale restent non validés ; ils dépendent de ce paquet. Q2/action-relative reste H:28, Q1 H:43. Aucun nouveau corpus, gel, score ou réservation, quarantaines et quatre événements exclus préservés. PC de Jeff non requis pour ces contrôles hors ligne.
