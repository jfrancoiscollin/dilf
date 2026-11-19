# MTDP — contrat de preuve FMJD pour les parties issues de PDN

**Statut : spécification de fondation, non implémentée et non exécutée.** Ce document n'accorde aucune admission D1 et ne modifie pas ses critères. Il définit la preuve manquante entre authentification des octets PDN et qualification d'une cohorte.

## Chaîne de preuve minimale

Pour chaque entrée candidate, exiger un identifiant de source PDN, le SHA-256 des **octets** du fichier source, un identifiant de partie déterministe et non ambigu, et la position attendue (FEN canonique, joueur au trait et index de demi-coup). Le producteur doit enregistrer la version du parseur, la révision du moteur FMJD, la révision du code et le schéma du manifeste. Une source introuvable, un champ absent, un doublon ambigu ou une discordance doivent entraîner un rejet explicite, pas une valeur par défaut.

1. **Authentifier la source** : relire les octets du PDN, calculer SHA-256 et vérifier l'empreinte déclarée. Le nom de fichier n'est jamais une preuve d'identité.
2. **Prouver l'appartenance** : parser le PDN authentifié et reconstruire un identifiant de partie à partir d'une règle déterministe publiée (par exemple index de partie dans le fichier + empreinte de sa représentation canonique). Vérifier que l'identifiant demandé désigne **une et une seule** partie réellement présente ; une simple concordance de métadonnées d'événement ou de joueurs est insuffisante.
3. **Rejouer légalement** : depuis la position initiale déclarée, appliquer chaque coup avec le moteur de règles FMJD épinglé ; contrôler captures obligatoires, chemins de prises, promotion et joueur au trait. Les ambiguïtés de notation et les chemins menant au même échiquier doivent être explicitement représentés ou mis en quarantaine, jamais résolus silencieusement.
4. **Lier chaque observation** : après chaque demi-coup, comparer l'index et la FEN canonique reconstruite avec l'observation revendiquée. Conserver la trace du chemin de coups et l'identifiant de la partie ; refuser tout décalage, coup illégal ou position introuvable.
5. **Séparer la qualification indépendante** : dédupliquer au minimum par partie, événement et position canonique + trait contre toutes les cohortes de développement/réglage et les réserves D1. Cette étape est distincte de la légalité et nécessite un inventaire versionné des corpus déjà utilisés.

## Preuves et sorties exigées

Un rapport machine-readable doit porter des champs distincts `pdn_bytes_verified`, `game_membership_verified`, `fmjd_legality_verified` et `independent_cohort_qualified`. Chacun n'est `true` qu'après vérification de **toutes** les lignes et conservation d'une preuve par partie/position ; l'absence de preuve impose `false`. Conserver le nombre total de parties, positions, doublons, ambiguïtés et rejets, les raisons par ligne, les SHAs des dépendances et les SHA-256 des sorties. La validation de la chaîne ne doit pas dépendre des scores Scan/Jass.

## Tests de régression préalables à l'admission

- PDN correct et partie réellement présente : preuve positive avec replay légal.
- Même SHA-256 de PDN mais `game_id` inventé : rejet d'appartenance.
- Partie présente mais FEN ou index falsifié : rejet de liaison.
- Coup illégal ou capture obligatoire omise : rejet FMJD.
- Deux parties indiscernables selon la règle d'identification : rejet d'ambiguïté.
- Même partie/position dans une cohorte de réglage ou un événement réservé : rejet d'indépendance.
- Fichier PDN modifié, digest absent ou révision moteur absente : rejet de provenance.

## Frontières de responsabilité

**Fondation H43** : spécifier et tester la preuve générique PDN→partie→coups légaux→positions avec FMJD, sans changer les signatures ni les expériences D1. **D1 H28** : décider des règles d'admission, de l'antifuite, des cohortes et de l'intégration à `admission_gate.py`. **H13 Jass** : réserver la comparaison décisionnelle prospective après qualification indépendante. Aucune nouvelle expérience, fusion, dépense ou exécution lourde n'est autorisée par ce document.
