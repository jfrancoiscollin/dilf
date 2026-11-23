# Corpus Jass historique récupéré

Onze fichiers du manifeste historique du **20 juin 2026**, retrouvés et extraits
le **23 novembre 2026** depuis un disque Ubuntu arrêté, en lecture seule.

**16 610 792 enregistrements JNNW**, pour **159 595 365 octets compressés**.
Les fichiers gzip d'origine sont conservés sous `objects/`.
Leur provenance dans l'ancien dépôt est donnée dans `manifest.json` et dans
`historical-source-manifest.txt`. Les chemins Windows personnels et identifiants
du disque local sont omis.

Les onze fichiers sont distincts par leur contenu brut et aucun de leurs
SHA-256 bruts n'est présent dans le lot R2 du 21 novembre déjà publié ici.
Cela ne prouve pas que les positions individuelles sont disjointes.

## Vérification locale

```text
python verify_snapshot.py
```

Le vérificateur contrôle les empreintes des fichiers compressés et décompressés,
les tailles, la signature JNNW et les nombres d'enregistrements. La lecture
gzip complète contrôle également le CRC. Aucune connexion externe n'est requise.

Les nombres correspondent au manifeste historique : malgré son titre « corpus
30M », ce manifeste énumère réellement **16 610 792** enregistrements.
Il ne fournit pas de SHA-256 original indépendant ; les empreintes publiées
documentent les octets récupérés. La légalité FMJD n'a pas été évaluée par moteur.

Le format JNNW est décrit dans le [lot R2](../2026-11-21/README.md).
Cette récupération ne contient pas le corpus HOME1044 UNIFORM de 40 millions,
qui reste non retrouvé. Elle ne relance aucun self-play ni aucune expérience D1.
