# Q3 — Grille historique des coûts et du regret, 28 novembre 2026

**Diagnostic rétrospectif, pas nouvelle validation indépendante.** Plan `17e7cc2ab65ffefdc99ba48ca21d65181187c475` publié avant le calcul des différences entre budgets ; les résultats agrégés et scores de cette population étaient déjà connus. Aucun score acquis, moteur, nouveau candidat ou gel. Question Q3 : existe-t-il sur cette grille un point à moins de nœuds et regret moyen observé non supérieur au natif 50k ?

## Résultat

**Aucun des neuf points n’est moins coûteux avec absence de hausse moyenne observée par rapport au natif 50k.** Les trois points 10k consomment 80 % de nœuds en moins, mais augmentent le regret moyen de **64/38 = 32/19 = 1,684211 unité Scan**, dégradent 9 positions, en améliorent 3 et en laissent 26 égales ; plus forte hausse individuelle +25. La marge descriptive fixée était 0, sans prétention de test de non-infériorité.

À 50k, LCB améliore une position de 11 unités de regret, sans réduction de nœuds ; le contrôle et le natif sont égaux. À 200k, la moyenne baisse de94/38 = 2,473684 unités, au prix de 4x les nœuds, mais deux positions se dégradent. Un budget plus élevé ne garantit donc pas une amélioration par position sous cette référence empirique.

| Budget | Bras | Ratio nœuds / natif 50k | Regret moyen | Δ regret moyen | Meilleures / égales / pires | Hausse max |
|---:|---|---:|---:|---:|---:|---:|
|10000|native_full|0.2|10.210526|+1.684211|3 / 26 / 9|25|
|10000|control|0.2|10.210526|+1.684211|3 / 26 / 9|25|
|10000|LCB_full|0.2|10.210526|+1.684211|3 / 26 / 9|25|
|50000|native_full|1|8.526316|+0.000000|0 / 38 / 0|0|
|50000|control|1|8.526316|+0.000000|0 / 38 / 0|0|
|50000|LCB_full|1|8.236842|-0.289474|1 / 37 / 0|0|
|200000|native_full|4|6.052632|-2.473684|9 / 27 / 2|12|
|200000|control|4|6.052632|-2.473684|9 / 27 / 2|12|
|200000|LCB_full|4|6.052632|-2.473684|9 / 27 / 2|12|

Toutes les lignes et rapports par arène sont conservés dans le JSON, y compris résultats nuls et défavorables. Les deux témoins 200k de non-monotonie sont D9PF2OSW partie 59 (regret 19 contre 7 au natif 50k, +12) et s7ahYqL4 partie 146 (11 contre 8, +3), pour chacun des trois bras. Ils ne constituent pas de nouvelles parties indépendantes.

## Méthode et portée

Joindre les **38 mêmes positions, 31 parties propriétaires, deux arènes, trois budgets** ; les 342 cellules des trois bras originaux sont raccordées aux 114 reçus de nœuds. Les 38 positions ne deviennent ni 114 ni 342 observations indépendantes. Les propriétaires et maxima Scan16 sont identiques entre budgets, coups choisis raccordés, nœuds réellement mesurés et plafonds complets vérifiés. Pour le contrôle, recherche principale + vérification = budget total ; le natif et LCB utilisent chacun le budget entier. Les bras résiduels supplémentaires ne sont pas inclus dans cette comparaison de coût total.

Les trois JSON sources et leurs SHA sont authentifiés au snapshot 41783f7, avec la preuve CI fermée de la réconciliation initiale. Aucune relecture nouvelle de référence moteur : seulement les résultats dérivés déjà publics. Le champ historique covered signifie égalité au meilleur score, pas disponibilité de la référence ; le raccordement le vérifie comme indicateur d’optimalité. Les sommes et ratios sont exacts, les moyennes JSON sont des fractions ; aucun bootstrap/intervalle neuf ni sélection postérieure de budget.

Unités entières Scan (0,01 HUB), pas pions matériels calibrés. Scan16 est empirique, pas minimax. Toutes les cellules concernées sont ordinaires ; aucune catégorie non ordinaire n’est transformée en regret numérique. **Aucune vérité WDL exacte disponible ni préservation WDL établie. Aucun temps complet utilisable** : le coût relatif en nœuds ne devient pas une économie de secondes, mémoire ou Elo.

Le résultat exclut seulement une prétention de réduction sans hausse moyenne observée sur **ces neuf points**. Une hausse moyenne positive ne prouve pas qu’elle soit statistiquement significative ou inacceptable ; aucune tolérance non nulle n’est choisie après résultat. Un compromis avec regret toléré exigerait une question distincte et un seuil annoncé avant de nouvelles références. Il n’exclut pas un autre budget, une autre méthode ou population ; il ne prouve ni non-infériorité ni infériorité future. Aucun point n’est promu comme candidat Q1/Q2, même celui à meilleure qualité moyenne.

## Validation et suite

**85 tests locaux passent, dont 11 nouveaux** : coûts de vérification facturés, bras résiduels exclus, identités appariées, catégories non numériques, optimum/score/racine raccordés, différence entre sûreté individuelle et moyenne. Deux calculs défaut/731 identiques à l’octet. Résumé et toutes lignes : `validation/q3-archived-budget-quality-2026-11-28.json`. **CI hors ligne confirmée** : implémentation `2e0d684`, [Actions 46164508676](https://github.com/jfrancoiscollin/dilf/actions/runs/46164508676), job 141038953551 success : 85 tests et cmp du rapport complet. Artefact 15271061875 téléchargé, ZIP 20403 octets SHA-256 4990f2243162757110cca0390db7ea7b2f6558429989ae48f79dcf60465b9e20 conforme GitHub ; rapport 383398 octets SHA-256 03d610fb9613b814c2956b9b20810c923e9a2001b6c772dd24ad1ea377c9c95b identique aux deux runs locaux. ZIP et reçu CI structurés versionnés dans validation/ ; aucun moteur ni nouvelle référence acquis.

**Décision Q3 : fermer ce diagnostic sur la grille connue, ne pas répéter les arènes ni inventer une courbe monotone/coût à qualité égale.** Attendre le paquet candidat Q1/Q2 indépendant avant intégration chaude et comparaison prospective ; fixer alors qualité, budgets et tolérances avant nouvelles références. Q2/action-relative et admission H:28, Q1 H:43, Q3 H13 ; quatre événements réservés, cohortes et quarantaines inchangés. Aucun nouveau score/signature/top-K/dimension, corpus, gel ou réservation. PC Jeff non requis pour ces contrôles hors ligne.
