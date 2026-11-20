# H13 — réconciliation du cache historique d'exclusions

**Audit d'artefact existant, sans nouveau rejeu moteur ni score cible. Aucun nouveau gel.**

Source : run [44730344598](https://github.com/jfrancoiscollin/dilf/actions/runs/44730344598), artefact `14625817620` téléchargé et vérifié (10 753 699 octets, SHA-256 `2768da137051e006a96b2fb0ac5b58ff5778e53fb0371d9fcd982a3948852165`). Seuls les trois membres d'exclusions/index historiques ont été lus par le producteur ; chacun correspond à son empreinte préexistante. Les autres membres, notamment le smoke d'ingénierie, ne sont pas utilisés.

| Quantité réconciliée | Nombre |
|---|---:|
| Sources PDN | 23 |
| Enregistrements de parties | 4 616 |
| Enregistrements à rejeu complet | 4 434 |
| Trajectoires complètes distinctes | 4 276 |
| Doublons parmi les rejeux complets | 158 |
| Parties en quarantaine | 182 |
| FEN de préfixes légalement confirmés | 433 363 |
| Identifiants publics Lidraughts | 4 582 |
| Empreintes de notation normalisée | 4 458 |

Les comptes s'équilibrent : `4 616 = 4 434 + 182` et `4 434 = 4 276 + 158`. Les statuts locaux totalisent 4 281 « indexed », 153 « duplicate » et 182 « quarantined ». Les cinq trajectoires complètes de l'extension P1RUlfJc déjà présentes dans l'histoire expliquent l'écart entre 4 281 indexations locales et 4 276 trajectoires uniques globales. Aucun de ces effectifs n'est présenté comme un nombre d'observations indépendantes.

Le producteur vérifie tous les identifiants fichier:index attendus, les statuts par partie, l'absence de trajectoire certifiée pour une quarantaine, l'union exacte des empreintes complètes, la conservation des FEN antérieures et les IDs publics des sources réservées effectivement présentes. Les 247 fichiers de positions historiques antérieurs représentent 188 809 FEN dans l'inventaire de départ ; leur inclusion dans les ensembles successifs est vérifiée. Les FEN de parties ambiguës sont limitées aux préfixes confirmés : aucune continuation n'est inventée.

## Lacune de couverture identifiée

Le cache comprend fFgE7oED et P1RUlfJc, **mais pas s7ahYqL4 ni D9PF2OSW parmi ses sources** : 147 + 61 = **208 parties** supplémentaires restent à réconcilier pour cette extension historique. Cela n'affirme pas que toutes leurs FEN sont absentes : des positions communes peuvent déjà figurer dans le cache. Cela interdit de certifier la couverture complète de leurs exports entiers.

Les quatre événements restent protégés par le précontrôle H13 source/public-ID/notation déjà validé. Cette protection ne remplace pas l'extension du registre FEN/trajectoires, ni la réconciliation des autres manifestes/alias. `complete_historical_exclusion_registry=false` et `independent_cohort_qualified=false` sont conservés.

## Reproduction

Après téléchargement de l'artefact ZIP indiqué :

```bash
python -m research.mtdp.historical_exclusion_inventory_audit --root . --archive ARTIFACT.zip --output /tmp/historical-reconciliation.json
cmp /tmp/historical-reconciliation.json research/mtdp/validation/historical-exclusion-reconciliation-2026-11-20.json
python -m pytest -q research/mtdp/tests/test_historical_exclusion_inventory_audit.py
```

Les artefacts Actions expirent ; le workflow existant peut reproduire ces trois membres à partir des entrées historiques archivées et du FMJD épinglé. Pour auditer un nouveau ZIP, fournir ensemble `--expected-archive-sha256`, `--source-run-id` et `--source-artifact-id` d'après ses métadonnées GitHub. Le conteneur/provenance changera alors, mais **les trois empreintes internes restent obligatoires**. Les tests CI sont synthétiques et hors moteur ; l'audit complet du ZIP téléchargé a été exécuté localement, pas présenté comme un nouveau résultat moteur.

Prochaine action D1/H43/H13 : étendre la couverture historique aux deux exports clos réservés, conserver les quarantaines et doublons, puis vérifier les autres corpus/alias avant toute qualification indépendante et tout nouveau protocole/gel. Aucun besoin d'allumer le PC de Jeff pour cet audit.


**Complément du même jour :** la lacune des208 parties a été traitée par le rejeu historique FMJD, sans nouveau scoring. Voir `CLOSED_RESERVED_EXCLUSIONS_2026-11-20.md` :200 rejeux complets,8 quarantaines ; cache étendu à25 sources/4 824 parties et452 526 FEN confirmées. Le présent audit de la base23 sources reste inchangé comme preuve de départ. La qualification indépendante globale reste refusée.
