# H13 — Oracle historique sans dame au trait, 26 novembre 2026

Protocole et périmètre publiés avant les appels légaux : 065d39d5c3d3cb6907772a423bffb03596b805a7. Tête initiale 7bb8d2e, PR43 ouverte/draft, neuf contrôles success, aucun équivalent actif/en attente. Trois vieux jobs CI/compatibilité en attente sur d’anciennes têtes sont sans rapport avec ce calcul et conservés.

**384 622 FEN supplémentaires sans dame du côté au trait : zéro désaccord ancien/Jass ou corrigé/Jass, zéro différence de racines/chemins entre ancien et corrigé, zéro ajout/retrait/régression et zéro double clé Jass.** La concordance corrigé/Jass des racines légales couvre désormais les **455 582 FEN historiques du registre connu**, en réutilisant les preuves des 52 010 avec dame au trait et des 18 950 sans dame active déjà contrôlés. Les omissions de retour de dames identifiées antérieurement ne sont pas effacées : l’ancien générateur n’est pas déclaré correct sur tout le registre.

## Périmètre et méthode

Registre conservateur immuable des 25 sources connues, cohérent avec les rejeux corrigés des 4 634 dossiers stricts et 190 quarantaines. Sélection exclusivement par trait/dames et couverture légale antérieure, aucune lecture de scores ou signatures. Une dame adverse n’exclut pas les pions actifs. Aucune position exclusivement fraîche introduite. Des 403 572 FEN sans dame au trait, retirer les 18 950 déjà couverts donne 384 622 nouveaux contrôles.

Résumé figé validation/nonking-oracle-scope-2026-11-26.json, SHA-256 0dc8ad714e029d19c6e342aa45e26d3d14158e726d5f9fd4ab74098af01cfb79. Liste canonique triée/LF final : 27 912 229 octets, SHA-256 4e3be05f836fa86d947937a55902dcd52f53651176dded2241e46f41bccb3b2d. Le runner réauthentifie les sources, les preuves antérieures et tous les octets/compte/digest de sélection avant les générateurs.

Ancien FMJD 0e5189fbb251bf5eaf2e613d0f878bb17c740311, king-origin-v1 explicite/source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d et Jass légal cfe07fce6385b980553a898e9651d53419589ebc inchangés. Exporteur légal existant, aucun évaluateur/recherche. Ensembles de racines origine/destination/pièces prises/promotion comparés intégralement ; chemins Python comptés et hachés séparément. Lots de 1 000, délai 30 s/appel. Traces écrites progressivement sur disque avec empreinte incrémentale, sans accumulation du ledger complet en mémoire. Un désaccord scientifique serait conservé comme témoin, pas supprimé pour faire passer le job.

## Validation et reproduction

Deux calculs locaux complets, hashseeds défaut et 731, sans désaccord et identiques à l’octet pour les cinq sorties sémantiques. 23 unittest passent : sélection typée, provenance altérée, périmètre tronqué/remplacé, digests incrémentaux et ouverture exclusive des sorties, indices entre lots, régressions/témoins, parser légal et correction isolée. Deux sélections structurelles défaut/731 terminées. La reproduction Actions est limitée à un seul calcul sous hashseed 731, conformément au protocole ; CI à confirmer.

```sh
python -m research.mtdp.nonking_oracle \
  --root . --cache historical-input/four-reserved-events-exclusions.json \
  --corrected-inventory corrected-input/possible-board-inventory.jsonl \
  --adapter fmjd --jass jass --executable /tmp/mtdp-nonking-build/mtdp_jass_legal_catalogue \
  --output-dir result
python -m unittest research.mtdp.tests.test_nonking_oracle_scope \
  research.mtdp.tests.test_nonking_oracle \
  research.mtdp.tests.test_king_origin_inventory_impact \
  research.mtdp.tests.test_return_capture_oracle \
  research.mtdp.tests.test_king_origin_correction
```

Le workflow restaure le cache depuis le run historique 45791384527 (hash interne épinglé) et l’inventaire corrigé du run 45768311500. Le rapport versionné validation/nonking-oracle-2026-11-26.json (2 192 octets, SHA-256 f4a0bc13d397fcc78b2605217ae02b6d66fe602286eba9fc02f7fa92f329acad) lie les gros fichiers de l’artefact : ledger 353 042 474 octets SHA-256 6253a177ced3c3b9961d8e253faf8eeaa25eacda63ac41001a22ab3f5ca21763 ; catalogue brut 51 374 124 octets SHA-256 fbaceb63c30c69fa50d68d4b1e4599018abfe5e5aaf54a21cb362f59d774a524 ; témoins vides SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. La provenance compilateur/binaire reste séparée des comparaisons sémantiques.

## Limites et suite

Cette concordance couvre les **racines légales des 25 sources historiques connues**. Elle ne prouve ni complétude globale MTDP, ni règles universelles, ni identité de chemin joué, ni meilleur coup ou équivalence minimax. Une racine commune ne certifie pas encore indépendamment le plateau successeur de deux moteurs. Aucun score ancien recalculé, aucune nouvelle efficacité revendiquée. Cache, moteur par défaut, anciens résultats, 190 quarantaines et frais 145/7 conservés ; quatre événements réservés exclus. uDIrrl1c entier brut non admis, aucune nouvelle réservation H13, aucun split/gel/signature/top-K/dimension. Licence/provenance/indépendance fraîche restent des portes D1 séparées.

Après preuve CI, ne plus refaire ces périmètres de racines clos. Prochain contrôle H13 justifié : délimiter et préenregistrer un contrôle ciblé des **successeurs typés Python/Jass** pour retours de dames, prises multiples et promotions, à partir de témoins historiques/synthétiques explicites, sans transformer des données déjà scorées en cohorte prospective. PC de Jeff non requis pour le calcul présent.
