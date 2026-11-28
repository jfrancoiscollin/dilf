# Repérage H13 pour la preuve H43 PDN→partie→FMJD

Repérage du 20 novembre 2026, sur `8347f7a15ca64bdb665cb8ba7005481da480c8db`. Complément de `FMJD_PDN_MEMBERSHIP_PROOF_SPEC.md`, **pas une implémentation du validateur**, une admission ou une nouvelle expérience. H43 conserve la preuve générique ; D1 son intégration/admission ; H13 le protocole prospectif Jass/Scan, le budget total et les réservations après qualification.

## Briques déjà présentes dans DILF

| Besoin H43 | Entrée existante | Contrat observé dans le code |
|---|---|---|
| Parser les parties | `research/mtdp/pdn.py:parse_games(pdn)` | Texte → liste de `PdnGame(index, tags, moves)` ; index à partir de 1 ; lignes principales, commentaires/variantes retirés ; notation non supportée rejetée. |
| Lire un fichier existant | `research/mtdp/pdn.py:read_games(path)` | Lit en UTF-8 avec BOM optionnel, puis appelle `parse_games`. Relit le chemin ; ne vérifie pas le hash des octets. |
| Résoudre chaque coup légal | `research/mtdp/pdn.py:_resolve(state, token, engine)` | Compare aux coups de `engine.legal_moves`. Une prise avec chemin explicite doit correspondre au chemin entier. Zéro ou plusieurs correspondances → `PdnReplayError`. Ne pas appeler cette fonction privée comme nouvelle API publique ; utiliser le rejeu. |
| Rejouer atomiquement | `research/mtdp/pdn.py:validated_trajectory(game, engine)` | Matérialise tout `replay_game` ; renvoie `(ply, token, state)`, **y compris le ply initial 0**, ou lève une erreur sans renvoyer de trajectoire partielle. FEN initiale prise du tag FEN si présent, sinon position initiale. |
| Brancher le vrai moteur | `research/mtdp/draught_master_adapter.py:create_engine()` | Importe tardivement `backend.game_engine` puis construit `DraughtMasterRules`. Ajouter la **racine du dépôt draught-master** au `PYTHONPATH`, pas seulement son dossier backend. |
| Interface de règles consommée | `DraughtMasterRules.legal_moves/apply_move` | L'adaptateur appelle `get_legal_moves(native_state)` et `apply_move(native_state, native_move)` du moteur ; conversion des pièces/rois/trait. `apply_move` exige un coup légal unique, pas une simple translation de cases. |
| Canoniser l'observation | `pedagogy.game.state_to_fen(state)` | Sérialiser l'état rejoué ; comparer trait, types de pièces et occupation à la FEN attendue. D1 possède `decision_equivalence.fmjd_fen.canonical_fen` pour les alias syntaxiques, ce qui ne remplace pas le rejeu. |
| Export atomique historique | `research/mtdp/trajectories.py:export_games` | Valide chaque partie avant émission, quarantaine par partie. Les identifiants `game-{index}` sont **relatifs au fichier**, pas une preuve indépendante d'appartenance. |

## Point de départ CI réel

`.github/workflows/downstream-compat.yml` extrait `jfrancoiscollin/draught-master` au commit **`0e5189fbb251bf5eaf2e613d0f878bb17c740311`**, installe ses dépendances, puis lance `research.mtdp.trajectories` avec :

```text
PYTHONPATH=<racine dilf>:<racine draught-master>
--engine-factory research.mtdp.draught_master_adapter:create_engine
```

Le workflow `.github/workflows/mtdp-d1-score-blind-pcblues.yml` réutilise cet adaptateur dans `decision_equivalence.fmjd_export`. Ces replays historiques sont déjà opérationnels en CI ; **ils ne prouvent pas l'appartenance d'un identifiant demandé à une nouvelle source authentifiée**. Les 26 parties / 1864 positions historiques ne constituent pas la nouvelle cohorte indépendante.

## Liaison qui reste à implémenter par H43, puis à intégrer par D1

1. Authentifier les **octets** du PDN et parser exactement ce contenu (par exemple `parse_games(raw.decode('utf-8-sig'))` après calcul/vérification de son SHA-256). Un hash obtenu sur un contenu puis un second chargement non lié ne constitue pas cette preuve.
2. Figer et tester la règle d'identification d'une partie dans cette source : le couple source authentifiée / index, et l'empreinte canonique prévue par le contrat H43. Ne pas déduire l'appartenance du seul `GameID`, `Site`, événement ou nom de fichier. `fmjd_export.export_records` utilise actuellement `GameID`/`Site`/index pour un export historique, sans prétendre fournir cette preuve.
3. Exécuter la trajectoire entière avant de valider une observation ; vérifier le ply demandé, la FEN canonique et le trait ; rejeter partie inconnue, index hors plage, FEN fausse, coup illégal et chemin ambigu. Conserver les preuves par partie/position et les révisions.
4. D1 raccorde cette preuve à sa porte d'admission et à son inventaire d'exclusions. Identité d'octets, appartenance, légalité et indépendance restent quatre propriétés distinctes ; elles ne passent pas à `true` par simple présence d'un schéma ou réussite de tests synthétiques.

## Tests existants et limite de cette vérification

Commande locale exécutée lors du repérage :

```bash
python -m pytest -q research/mtdp/decision_equivalence/test_clustered_bootstrap.py research/mtdp/tests/test_pdn.py research/mtdp/tests/test_draught_master_adapter.py
```

**12 tests et 3 sous-tests réussis.** Les tests parseur/adaptateur utilisent des règles factices contrôlées ; aucun rejeu local avec le vrai moteur, aucune preuve d'appartenance ni nouveau corpus n'est revendiqué. Le nouveau bootstrap D1 est couvert par la collecte automatique : CI D1 `44662604449`, job `136044177226`, **231 tests et 24 sous-tests réussis** ; les huit workflows du SHA de repérage sont réussis. Ce bootstrap D1 ne remplace pas la méthode figée H13 des résultats 114/38/31.

La prochaine action H43 peut donc partir de ces API existantes et écrire les fixtures de falsification du contrat, sans reconstruire un parseur ou lancer de Scan/Jass. H13 ne réserve aucune nouvelle cohorte ici. Les quatre événements entiers `fFgE7oED`, `P1RUlfJc`, `s7ahYqL4`, `D9PF2OSW` et toutes leurs parties/FEN restent exclus de D1 fitting/validation indépendante/signatures/top-K/raffinement/seuils/dimension.

## Mise à jour : preuve H43 et contrôle moteur réel

La preuve H43 est maintenant implémentée dans pdn_membership_proof.py (039b77f). Le commit H13 7865b4654e655b00b9294411f20585dae9f3eb35 ajoute seulement ses tests réels et leur raccordement au workflow existant. Run44673127249/job136078538102 :3tests réussis,aucun sauté,révision FMJD0e5189fbb251bf5eaf2e613d0f878bb17c740311 vérifiée. Cas synthétiques :occupation attendue après2coups,illégalité tardive rejetée même au ply0,capture obligatoire respectée. Les17tests unitaires ciblés locaux passent ;3tests réels locaux étaient sautés faute dépendance,distincts de leur exécution distante obligatoire. Les8workflows du code sont réussis. Preuve validation/pdn-membership-real-fmjd-2026-11-20.json. La liaison arbitraire manifest_game_id→source/index et la qualification indépendante restentfalse ;ces3cas ne constituent pas une admission de corpus. Prochaineporte H43/D1 :liaison game_id etinventairedindépendance,puisadmission avantcampagneH13.

## Lecture prospective stricte et dépendances historiques figées

Le durcissement post-résultat doit passer par `research.mtdp.pdn_strict.parse_games_strict`. Ce garde reprend les mêmes bornes de parties et annotations que le parseur historique puis rejette tout token de ligne principale après le résultat ; `pdn_membership_proof.prove_pdn_position` y raccorde les octets authentifiés. Les nouveaux manifestes doivent épingler aussi `pdn_strict.py`. Le fichier `pdn.py` lui-même est une dépendance octet-épinglée des études H13 archivées ; le modifier casse les preuves de publication et les replays, même si les données sont identiques. Il reste donc restauré à la version du gel3fa9a56a, sans changement des contrôles de hash ; ce choix de compatibilité ne doit pas être présenté comme une validation prospective de suffixes par le parseur historique. Les tests stricts corrigés sont dans `tests/test_pdn_strict.py`, avec de vrais sauts de ligne et un contrôle de la voie d’admission authentifiée.
