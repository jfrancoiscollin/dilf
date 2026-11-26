# H13 — Successeurs typés Python/Jass, témoins ciblés du 26 novembre 2026

Protocole et fixtures publiés avant les appels légaux : 3e7bd8960df1969a7418c8c55f4bf409ad2c6682. PR43 ouverte/draft à faf0cca, neuf contrôles success, aucun équivalent actif/en attente. Les campagnes de racines déjà closes ne sont pas relancées.

**20/20 plateaux concordants : 74 chemins Python, 69 racines uniques par parent (somme sur les 20 cas), aucun désaccord de successeur et aucune double clé Jass. Les 12 transitions attendues manuellement sont confirmées.** Les cinq racines associées à plusieurs chemins Python conservent explicitement tous leurs chemins ; chacun mène au même successeur typé que Jass. Aucun premier chemin n’est choisi pour lever les quarantaines.

## Ce qui est testé

Huit régressions antérieures inchangées : deux retours de dames historiques et leurs symétries, position initiale, boucle de pion, dame calme et bloqueur ami. Douze plateaux supplémentaires : six témoins structurels et leurs symétries (promotion calme de pion, promotion sur prise, passage sur la rangée de promotion puis sortie sans couronnement, prise double de pion, dame déjà couronnée jouant ou capturant vers sa rangée de promotion). Les 12 attentes de transitions sont figées dans le même fichier avant observation des moteurs. Les cas de promotion distinguent la promotion d’un pion du déplacement d’une dame déjà couronnée, même lorsqu’ils aboutissent au même type de pièce.

Fixtures : validation/fixed-successor-fixtures-2026-11-26.json, 5 366 octets, SHA-256 f0f6eef86932850612d2aff16c925e53d508422a2bbd690f0d63906bd9e47571. Témoins diagnostiques historiques/synthétiques, aucune population indépendante d’efficacité.

Le nouvel exporteur mtdp_jass_successor_catalogue appelle Position::after(move).to_fen() dans le checkout Jass cfe07fce6385b980553a898e9651d53419589ebc propre. L’adaptateur corrigé reste explicitement king-origin-v1/source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d au-dessus du FMJD 0e5189fbb251bf5eaf2e613d0f878bb17c740311. Toutes les racines origine/destination/pièces prises/promotion et tous les chemins Python sont conservés. La comparaison porte exclusivement sur l’occupation typée et le trait ; les compteurs 50-ply, répétitions et identité du chemin joué restent hors preuve.

## Validation et reproduction

17 unittest passent : dix nouveaux tests de transport et témoins scientifiques (chemins divergents sous une même racine, doublons, racine absente, mauvais trait, promotion/attente modifiée) plus sept régressions parseur/correction. Un successeur de trait ou type erroné mais syntaxiquement valide est conservé comme différence scientifique, jamais assimilé à une corruption de transport à corriger silencieusement.

Deux exécutions locales, hashseeds défaut/731, identiques à l’octet pour les trois sorties sémantiques. Le catalogue légal existant est inchangé : projection du nouveau format exactement égale au catalogue légal normal, et sortie également identique à celle de l’ancien binaire légal déjà construit, sur les mêmes 20 parents. Source et binaire légaux locaux inchangés (source cff961ffb64725c42928b6c747a4c7b6f0d32780654d8a5541a39f9767866bec ; binaire c4065367a315534284a3b9937b97fe51e2e2b011a26b2889ada435c0845aecfd). Seule une cible CMake de recherche supplémentaire est ajoutée, sans changement de production. CI ciblée à confirmer.

```sh
cmake -S jass -B /tmp/mtdp-successor-build -DCMAKE_BUILD_TYPE=Release \
  -DJASS_ENABLE_SIMD=OFF -DJASS_NATIVE=OFF \
  -DCMAKE_PROJECT_jass_INCLUDE="$PWD/research/mtdp/jass_preflight/targets.cmake"
cmake --build /tmp/mtdp-successor-build --target mtdp_jass_successor_catalogue mtdp_jass_legal_catalogue -j 2
python -m research.mtdp.fixed_successor_audit \
  --root . --adapter fmjd --jass jass \
  --successor-executable /tmp/mtdp-successor-build/mtdp_jass_successor_catalogue \
  --legal-executable /tmp/mtdp-successor-build/mtdp_jass_legal_catalogue \
  --output-dir result
python -m unittest research.mtdp.tests.test_fixed_successor_audit \
  research.mtdp.tests.test_return_capture_oracle research.mtdp.tests.test_king_origin_correction
```

Rapport complet versionné validation/fixed-successor-audit-2026-11-26.json : 58 376 octets, SHA-256 1dbcf3b40f3f353a831243fa4d67e73c2ae491024b5663635eeb8de918b59f1d. Catalogue successeurs brut : 3 050 octets, SHA-256 f659d49b319c531ddf4c5cd0292b4190eee1d5584e50e91726d2bfbe76232285 ; catalogue légal brut : 1 202 octets, SHA-256 e7c6d6861f40dd061dcf764fcaba52a7b8df28211b4ad573e5da3fd45a584f86. Provenances binaire/source/compilateur séparées des sorties sémantiques.

## Limites et suite

Ce contrôle ciblé ne prouve ni la concordance des successeurs sur les 455 582 FEN, ni un meilleur coup ou une équivalence minimax. Pas de généralisation statistique depuis ces témoins sélectionnés, pas de certification des chemins joués ni de levée des 190 quarantaines ou des sept ambiguïtés fraîches. Cache, règles par défaut, anciens scores, frais 145/7 et quatre événements exclus inchangés. uDIrrl1c entier reste candidat brut D1 non admis ; licence/provenance/indépendance restent portes D1 séparées. Aucun nouveau score/signature/top-K/dimension, split, gel ou réservation H13.

Après confirmation distante, prochain contrôle H13 justifié : dériver sans scores une liste de FEN historiques du registre connu possédant au moins une racine de retour à l’origine, promotion ou prise multiple, depuis les catalogues légaux déjà authentifiés ; retirer les témoins déjà contrôlés, publier le manifeste et préenregistrer l’extension des successeurs avant tout appel de transition. Réutiliser les preuves de racines au lieu de refaire leurs campagnes. PC de Jeff non requis.
