# Entrées historiques du rejeu CI

Archive durable **des entrées déjà vérifiées**, sans nouveau score ni nouveau corpus indépendant. Le rejeu d'anciennes parties ne dépend plus de la disponibilité HTTP de Lidraughts. Les vrais modules d'acquisition prospective et leurs gardes temporels restent inchangés.

Origine : [run44453019237](https://github.com/jfrancoiscollin/dilf/actions/runs/44453019237), artefact14496378916 téléchargé le19/11/2026 ; ZIP10752116octets, SHA-256 `6e66b724b6f97f5f98c945b50288c4c25eab4fb5b6b1a8e2bb827a4dcbaf3ca5`. Ce run avait passé les221tests et toutes les vérifications d'exclusion/rejeu. Le digest du ZIP récupéré a été vérifié avant extraction.

`pdn-inputs.zip` ne reprend que les18PDN de l'inventaire historique explicite `CARZrQpl/provenance.json`, les2copies originales concordantes de fFgE7oED et leurs reçus `downloads.json`. **19exports distincts,20copies**, sans score Scan/Jass. Chaque PDN brut a été comparé au SHA existant du protocole avant réarchivage ; CRLF/BOM conservés. ZIP déterministe1233115octets, SHA-256 `4c6b2941a4e18be4df016341f62de314657f215622440999843ea05ee58c5ed3`.

Le restaurateur vérifie le ZIP entier, l'inventaire exact sans doublons, chaque PDN et les reçus antérieurs avant toute écriture. Il refuse l'écrasement. Le journal s'appelle `archived-downloads.json` ; `archival-replay-restoration.json` précise zéro nouvelle requêteHTTP, `scientific_freeze=false` et l'origine exacte. Les deux copies restaurées ne sont **pas** présentées comme de nouveaux GET indépendants et n'autorisent aucun nouveau gel.

Diagnostic : le [run44472477627](https://github.com/jfrancoiscollin/dilf/actions/runs/44472477627), job135385061477, avait échoué avant tests après4URLError sur l'ancien export fFgE7oED. Relance ciblée135407312797 effectuée puis annulée automatiquement par les commits D1 concurrents ; aucun doublon ajouté. Le successeur44479968562 a ensuite réussi ses téléchargements : incident réseau transitoire, pas un résultat scientifique invalide. La restauration épinglée évite de répéter ce point de panne pour les mêmes entrées historiques ; tous les tests légaux, catalogues, exclusions, hashes et répétitions7/61 restent exécutés.

```bash
python -m research.mtdp.jass_benchmark.historical_replay_inputs --root . --output /tmp/historical-replay
```

Validation du correctif : [run44481263835](https://github.com/jfrancoiscollin/dilf/actions/runs/44481263835), job135413776831, **228tests passent**, toutes étapes réussies. Artefact14508886210 téléchargé/vérifié, ZIP10753702octets, SHA `8b17d9acbf06454d740e7f1972d43984f04227d0c18797ab78ef256d32e8f78e` ; vingt PDN/restauration vérifiés et cache complet des exclusions identique SHA `8dac5c60e1eaa10ff8e3e27f5c1fb0d0307edaeaec438e7c9bdc33b3e666dc32`. Paquets synthétiques7/61 identiques, toujours sans gel scientifique. Preuve complète `historical-replay-ci-verification-2026-11-19.json` au répertoire parent.
