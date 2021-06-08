$$
\newcommand{hmax}{h_{\text{max}}}
$$

# Suites possibles après avoir codé Dancing Links avec multiplicités

- [ ] Coder la résolution des contraintes dans un SAT Solver
- [ ] Améliorer la fonction objectif pour MILP pour privilégier ce qui est plus facile dans les solutions
  - [ ] Fusion possible avec OpenCV : faire jongler le plus possible de choses différentes, récupérer les enchaînements de lancers joués par le jongleur et privilégier ces enchaînements dans la fonction objectif (avec potentiellement des poids sur les enchaînements)
- [ ] Élaborer une heuristique efficace pour l'algorithme Dancing Links qui permet de construire rapidement les $n$ meilleures solutions
- [ ] Modifier l'algorithme M pour ne pas explorer l'arbre si la meilleure solution possible à partir de ce point est moins bonne que la meilleure solution rencontrée jusqu'à présent
  - [ ] Élaborer une fonction de score pour une solution (partielle) de l'algorithme M
- [ ] Amélioration de la résolution des contraintes par Dancing Links
  - [ ] Contraintes sur les mains
  - [ ] Balles non sonnées lors de leur réception
  - [ ] Balles silencieuses
- [ ] Améliorations à faire dans le programme
  - [ ] Transmettre les balles de l'algorithme directement au simulateur

# Contraintes liées au jonglage

- **Hauteur maximale des lancers** : 5 faisable à coup sûr, on peut encore monter jusqu'à 6/7 mais c'est plus difficile (on peut donc, si on autorise des lancers de 6/7 vouloir en minimiser le nombre)
- Contraintes sur les mains :
  - **Capacité maximale** : 4
  - Main avec 2 balles : on peut échanger facilement les deux balles
  - Main avec 3 balles :
    - on rattrape les balles avec les ~3 derniers doigts de la main
    - on lance uniquement la balle qui est du côté du pouce et de l'index
    - pour échanger les balles on effectue une rotation :
      - main droite : dans le sens inverse des aiguilles
      - main gauche : dans le sens des aiguilles
  - Main avec 4 balles :
    - on réceptionne une balle et elle se pose sur les 3 autres
    - la seule balle qu'il est possible de lancer est la balle du dessus
    - aucun échange de balle n'est possible
- **Enchaînements de lancers non réalisables** : aucun
- **Lancers multiplex non réalisables** : 1 avec tout autre lancer (la direction des mains est différente)
- **Remarques sur les lancers** :
  - il est difficile de faire sonner un lancer de 2 (il suffit d’interdire le lancer multiplex {2})
  - il est préférable de privilégier des lancers de 3/4/5 (plus esthétiques) dans les figures et éviter les lancers de 2

## Fonction objectif pour MILP

### On autorise les lancers de hauteur 6/7 mais on veut en minimiser le nombre

$$
\min\sum_{T, m} x_{T}^{m, 6} + x_{T}^{m, 7}
$$

### On privilégie des lancers de 3/4/5

$$
\max \sum_{T, m} x_{T}^{m, 3} + x_{T}^{m, 4} + x_{T}^{m, 5}
$$

## Balles non sonnées lors de leur réception

On pourrait introduire de nouvelles variables $y_{T(t, b, \hmax)}^{m, h}$.

## Codage des contraintes sur les mains avec Exact Cover

On introduit :

- De nouvelles variables :
  - $C_{t}$ pour tout temps $t$.
  - $B_{b, t}$ pour toute balle $b$ et temps $t$.

- Les couleurs :

  - $(m, i)$ pour toute main $m$ et position dans cette main $i$.
  - $p$ pour toute partition ordonnée $p$ de l'ensemble des mains.

- Les règles :
  $$
  x_{T(t, b, \hmax)^{m, h}} \Rightarrow B_{b, t+\hmax-h} : (m, 1)
  $$

  $$
  C_{t} : p \Rightarrow B_{b, t} : (m, i) \;\text{ pour toute balle } b \text{ telle  que } p[m][i] = b
  $$

  $$
  C_{t} : p \Rightarrow C_{t + 1} : p' \;\left\{\begin{array}{ll}\text{ telle que } p' \text{ est une configuration atteignable}\\\text{ depuis } p \text{ en une etape d'echange de balles}\end{array}\right.
  $$

  

La première règle permet que, quelque soit la configuration de la main avant de lancer la balle $b$ à l'instant $t + \hmax - h$, la balle $b$ est dans la main $m$ en position $1$. La seconde règle impose aux lancers de correspondre à la configuration car, dans le cas contraire, deux couleurs serait affectées à une même colonne. La troisième règle assure une cohérence dans la suite des configurations construites.