# Positions Jass sauvegardées depuis R2

Copie des corpus de positions et de leurs métadonnées présents dans le snapshot
local de `jass-data` du **21 novembre 2026**, publiée le 23 novembre 2026.
Les fichiers sont utilisables sans accès à R2 et sans identifiants Cloudflare.

## Contenu et provenance

`manifest.json` associe chaque clé R2 d'origine à un fichier sous `objects/`,
avec taille, ETag et SHA-256 de la source. Chaque contenu décompressé identique
est stocké une seule fois. Toutes ses sources restent dans le manifeste.
Les corpus différents peuvent partager des positions : la somme des lignes
ne représente pas un nombre de positions uniques.

- **FEN** : positions textuelles originales, commentaires et ordre conservés.
- **JNNW** : corpus binaires de positions annotées, compressés avec gzip.
- **JSM1/JSM2** : métadonnées binaires associées aux corpus, lorsqu'elles existent.
- **TSV** : tables de provenance, d'identité des positions ou d'annotations.

Les poids des modèles, les fichiers de configuration, les journaux, les objets
de compilation et les résumés agrégés ne font pas partie de cette publication.
L'import n'exécute aucun moteur et ne produit aucun nouveau résultat D1.

## Retrouver un fichier

Depuis ce dossier, cet exemple retrouve le corpus d'entraînement en FEN :

```python
import json
from pathlib import Path

root = Path(".")
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
source = next(s for s in manifest["sources"] if s["r2_key"] ==
              "inputs/t1bis-adj-g1/v1/conversion_pool_train_v2.fen")
positions = (root / source["object_path"]).read_text(encoding="utf-8").splitlines()
```

Pour un fichier `.gz`, utiliser `gzip.open(path, "rb")`. Les noms sous `objects/`
commencent par un préfixe du SHA-256 de leur contenu décompressé ; le manifeste
contient les empreintes complètes des contenus stockés et décompressés.

## Format JNNW

En-tête de 8 octets : signature ASCII `JNNW`, puis nombre d'enregistrements
`uint32` en little-endian. Chaque enregistrement contient 38 octets :
`struct.Struct("<QQQQBib")`, soit quatre bitboards (pions blancs, dames blanches,
pions noirs, dames noires), le trait (`0` blanc, `1` noir), un score `int32`
et un résultat `int8`. Les bits 0 à 49 correspondent aux cases 1 à 50.
La signification scientifique des scores et résultats dépend de la provenance
du corpus ; ce ne sont pas nécessairement des évaluations indépendantes.

## Vérification et limites

```text
python verify_snapshot.py
```

Cette commande locale contrôle les SHA-256, la décompression, les tailles et
les nombres d'enregistrements JNNW. Elle ne contacte aucun service externe.
Les octets des corpus sont conservés ; aucune normalisation ou déduplication
des positions à l'intérieur des corpus n'a été appliquée.
La validation du format ne prouve pas la légalité FMJD des positions.
Ne pas présumer d'identifiants de partie ou de transitions là où les métadonnées
ne les fournissent pas. Vérifier les chevauchements entre corpus avant de définir
des jeux d'entraînement, de validation ou de test.
