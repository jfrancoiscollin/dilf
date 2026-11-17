# MTDP-D1 — audit de préparation du gel (2026-11-17, 12:30 UTC)

**Statut : BLOQUÉ POUR LE GEL, non bloqué pour l'ingénierie.** Ce rapport est un audit documentaire score-blind, **pas une nouvelle cohorte** ni un résultat de classement.

## Évidence vérifiée
- Sur le commit `cf22a8f250d086ddf2223207f30ac28e6c96f6f5`, les sept workflows PR ont conclu `success`, dont D1 [run 44073899319](https://github.com/jfrancoiscollin/dilf/actions/runs/44073899319).
- L'artefact D1 du run est `14323078245`, digest ZIP `sha256:fd2a65ef07d2919db92c7f28bf35984d5e77a7fb8b466c9da0484f348cb90a75`. Il s'agit du rejeu **historique**, pas d'un nouveau corpus.
- Le code `registry_coverage.py` requiert cinq groupes : `pcblues_historical`, `scan_depth8`, `scan_depth12`, `jass_benchmarks`, `ffgE7oED_reserved`. Il valide présence, empreintes et lignes des fichiers **fournis** ; il ne découvre pas les sources manquantes.
- Le préenregistrement D1 interdit les 78 cibles réservées, toutes leurs parties, les parties et trajectoires déjà exploitées et les FEN connues ; il impose un gel antérieur aux scores Scan.

## Décision de contrôle
**Ne pas produire de manifeste de gel** à partir des seuls cinq noms de groupes. Un fichier synthétique qui satisfait `registry_coverage.verify` ne certifie pas la couverture des jeux historiques. Il faut vérifier pour chaque source : identifiant et version/commit, nombre de parties et positions, extraction des identités (partie, trajectoire complète, FEN), doublons intra/inter-sources, et empreinte du registre. Une source sans provenance complète est une exclusion à traiter comme non résolue, jamais comme vide.

Le contrôle des exclusions doit être exécuté sur la **réunion** des identités historiques et réservées, avec exclusion des parties entières contenant une cible fFgE7oED. La disjonction de parties propriétaires d'une paire historique ne suffit pas à établir l'indépendance d'un nouveau tournoi. Les résultats PC Blues (61 paires communes LCB/Q, trois propres à LCB) restent descriptifs et ne doivent pas alimenter une estimation indépendante de stabilité top-K.

## Critère de sortie et prochaine action
Établir un tableau de provenance vérifiable pour les cinq groupes, avec chemins réels, commit source, nombre de lignes et SHA-256, puis exécuter `registry_coverage.verify` et `cohort_exclusion_gate` sur une source de parties distincte **sans scores**. Publier le manifeste et son SHA dans un commit antérieur à tout calcul Scan. Tant qu'un groupe n'est pas réconcilié, le gel est interdit.

Aucun score Scan indépendant, aucun ordonnancement Jass D1 et aucun gain de calcul ne sont revendiqués.
