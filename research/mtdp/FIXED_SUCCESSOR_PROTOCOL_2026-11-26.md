# H13 — Successeurs typés Python/Jass : témoins ciblés, 26 novembre 2026

Préenregistrement avant exécution des générateurs ou transitions sur les nouveaux témoins. PR43 ouverte/draft à faf0ccaa63429bdf2310dda55574a287ecf4af98, neuf contrôles success ; aucun équivalent actif/en attente, ancien job CI en attente sans rapport préservé. Le contrôle des racines du registre connu est clos, il ne sera pas refait.

## Périmètre fixe

20 FEN distinctes, conservées dans validation/fixed-successor-fixtures-2026-11-26.json, 5 366 octets SHA-256 **f0f6eef86932850612d2aff16c925e53d508422a2bbd690f0d63906bd9e47571**. Huit régressions existantes inchangées (deux retours historiques, symétries, état initial, boucle de pion, dame calme, bloqueur ami), puis six témoins structurels et leurs symétries rotation 180°/couleurs inversées : promotion calme de pion, promotion sur prise, passage par rangée de promotion suivi d’une sortie sans couronnement, prise double de pion, dame déjà couronnée en rangée de promotion en coup calme et en prise. Douze transitions occupation/trait attendues sont fixées manuellement dans le même fichier avant observation des sorties. Toute attente réfutée reste rapportée, jamais retouchée pour obtenir un succès.

## Méthode

Mêmes versions : FMJD historique 0e5189fbb251bf5eaf2e613d0f878bb17c740311, correction explicite king-origin-v1/source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d ; Jass cfe07fce6385b980553a898e9651d53419589ebc. Nouvel exporteur isolé mtdp_jass_successor_catalogue via Position::after(move).to_fen(), sans toucher au format/exporteur légal existant ni aux règles par défaut. Racine = origine/destination/pièces prises/promotion normalisée à une promotion de pion, jamais un nouveau couronnement d’une dame existante.

Pour chaque FEN comparer toutes les racines corrigées/Jass, puis chaque successeur corrigé de CHAQUE chemin Python contre le successeur Jass de la racine correspondante. Conserver multiplicité des chemins, ensembles de successeurs par racine et doubles clés Jass ; aucun premier chemin arbitraire. Identité contrôlée : occupation typée + trait uniquement ; compteurs 50-ply, répétitions et identité du chemin joué exclus. Vérifier séparément les 12 attentes manuelles. Rapporter chaque désaccord et les actions associées ; une différence scientifique n’est pas un échec technique à masquer.

## Validation, sorties et suite

Parsers : refus de lignes manquantes, mauvais parent, clés/FEN invalides ; une différence légale de successeur/trait reste un résultat scientifique. Tests adversariaux de chemins divergents sous une même racine, double clé, racine manquante, promotion/couronnement, et conservation des attentes fixées. Deux exécutions locales hashseeds défaut/731 et une reproduction Actions 731 ; comparaison de tous les octets sémantiques. Conserver rapport, catalogue brut, provenance source/binaire/compilateur séparée ; vérifier que le catalogue légal initial est inchangé pour les mêmes 20 parents.

Aucun score, recherche, signature, top-K, dimension, split, gel ou nouvelle cohorte indépendante. Témoins diagnostiques historiques/synthétiques, pas confirmation d’efficacité. Aucun gain minimax ou meilleur coup revendiqué, pas de généralisation aux 455 582 FEN ni de complétude historique globale. Quatre événements réservés exclus, uDIrrl1c entier brut non admis, 190 quarantaines et frais 145/7 inchangés ; D1 garde ses portes licence/provenance/indépendance. PC de Jeff non requis si les ressources distantes existantes aboutissent.
