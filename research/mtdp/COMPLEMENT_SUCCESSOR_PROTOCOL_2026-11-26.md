# H13 — Complément historique des successeurs, 26 novembre 2026

Préenregistrement après délimitation structurelle, avant tout appel de transition sur ce complément. PR43 ouverte/draft à 9d1390fcb4fade950194f27ad9fe7e70fa6c978e ; neuf contrôles success, aucun équivalent actif/en attente. Vieux job CI en attente sans rapport préservé.

## Population fixée

Quatre catalogues légaux authentifiés, 468 231 FEN distinctes dont exactement 455 582 du registre historique connu ; 12 649 hors registre exclus. Retirer les 24 561 FEN historiques déjà validées en successeurs (24 558 parents à risque et trois des 20 témoins ciblés présents au registre). Reste **431 021 FEN**, **3 576 681 racines légales**. Aucun parent déjà clos ne sera rejoué. Aucun coup du complément n’a de tag retour à l’origine, promotion de pion ou prise multiple ; ce fait est contrôlé durant la dérivation sans nouveau générateur. Les dames adverses ou au trait sont autorisées selon les parents connus, sans changer la règle d’exclusion.

Résumé figé validation/complement-successor-scope-2026-11-26.json SHA-256 2f12d7dfd9c330edab6bd3a2e17f72744a8f0d53cfab3748a041428da183971e. Il lie le manifeste complet (FEN, catalogue d’origine, toutes les racines légales) et la liste triée/LF final à leurs tailles et SHA-256. Dérivation triée en flux, couverture exacte du registre et exclusions vérifiées. Aucun score, rang ou signature utilisé ; aucune association fictive de parties indépendantes.

## Méthode et traces

Même factory explicite king-origin-v1/source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d sur FMJD 0e5189fbb251bf5eaf2e613d0f878bb17c740311 ; Jass cfe07fce6385b980553a898e9651d53419589ebc, exporteur de successeurs et wrapper isolé inchangés. targets.cmake et toutes méthodes historiques gelées restent intacts.

Comparer toutes les racines calculées aux listes légales authentifiées, puis CHAQUE chemin Python et son successeur typé à la racine/successeur Jass. Aucune sélection de premier chemin, aucun échantillonnage. Identité contrôlée : occupation typée + trait ; nulle/répétition/chemin joué hors preuve. Lots au plus 1 000, délai 30 s/appel. Lecture et écriture progressives avec digests pour limiter la mémoire et espace disque de travail suffisant. Le ledger de chaque parent conserve compteurs, verdicts et empreintes des listes complètes de successeurs/racines et chemins ; catalogue Jass brut intégral et témoins détaillés de TOUS les désaccords conservés. Ces digests sont calculés après comparaison complète, jamais utilisés pour remplacer le calcul de transitions.

Deux dérivations et deux exécutions locales complètes, hashseeds défaut/731 ; une reproduction Actions 731 avec comparaison de chaque sortie sémantique aux deux locales. Tests de couverture/exclusion/ordre, intégrité du manifeste avant moteur, capture de divergences même si les racines concordent, et vérification des listes réellement consommées en flux. Un désaccord scientifique est rapporté sans retrait/adaptation ; les seuls échecs techniques sont corrigés et relancés sur le même périmètre. Conserver provenance binaire/source/compilateur séparée.

## Portée et coordination

Une concordance complète, combinée aux preuves antérieures disjointes, permettra de fermer les successeurs occupation+trait des **455 582 FEN des 25 sources connues**, pas de tout l’historique MTDP ni des règles universelles, compteurs ou minimax. Aucune nouvelle preuve de meilleur coup, recherche, score, signature, top-K, dimension, split, gel ou cohorte prospective. Les conclusions décisionnelles closes et budgets fixés restent inchangés. uDIrrl1c entier reste brut non admis ; D1 garde licence/provenance/indépendance fraîche. Quatre événements réservés exclus ; cache/règles par défaut/anciens scores/190 quarantaines/frais 145-7 préservés. Aucune nouvelle réservation H13. PC de Jeff non requis si les calculs bornés aboutissent sur les ressources distantes existantes.
