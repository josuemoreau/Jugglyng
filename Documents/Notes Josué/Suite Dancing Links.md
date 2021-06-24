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

# Idées

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

### Première version

On introduit :

- De nouvelles variables secondaires :
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

**Problème :** Ce n'est pas une bonne idée, il y a un nombre exponentiel de configurations de mains. Avec 10 balles et 4 mais ce nombre est déjà bien trop grand pour être calculé efficacement.

### Seconde version

On introduit :

- De nouvelles variables primaires :

  - $B_{b, t} \in \{1\}$ pour tout temps $t$ et toute balle $b$.

- De nouvelles variables secondaires :

  - $P_{t, m, i}$ pour tout temps $t$, main $m$ et position $i$.

- De nouvelles couleurs :

  - $b$ pour toute balle $b$.

- Les règles :
  $$
  x_{T(t, b, \hmax)}^{m, h} \Rightarrow P_{t + \hmax - h, m, 1} : b
  $$

  $$
  P_{t, m, i} : b \Rightarrow P_{t + 1, m, (i - 1) \% K} : b
  $$

  $$
  P_{t, m, i} : b \Rightarrow P_{t + 1, m', i} : b \text{ pour toute position } i \text{ et } m' \neq m
  $$

  $$
  P_{t, m, i} : b \Rightarrow B_{b, t}
  $$

La dernière règle impose de choisir exactement un emplacement pour chaque balle à chaque instant.

### Troisième version

On introduit :

- De nouvelles variables primaires :

  - $B_{b, t} \in \{1\}$ pour tout temps $t$ et toute balle $b$.

- De nouvelles variables secondaires :

  - $P_{b, t}$ pour tout temps $t$ et balle $b$.

- De nouvelles couleurs :

  - $(m, i)$ pour toute main $m$ et position $i$.

- Les règles :
  $$
  x_{T(t, b, \hmax)}^{m, h} \Rightarrow P_{b, t + \hmax - h} : (m, 1)
  $$

  $$
  x_{T(t, b, \hmax)}^{m, h} \Rightarrow B_{b, t'} \text{ pour tout } t \text{ tel que } t + \hmax - h < t' < t + \hmax
  $$

  $$
  P_{b, t} : (m, i) \Rightarrow P_{t + 1, b} : (m, (i - 1) \% K)
  $$

  $$
  P_{b, t} : (m, i) \Rightarrow B_{b, t}
  $$

  $$
  P_{b, t} : (m, i) \Rightarrow P_{t + 1, b} : (m', i) \text{ pour } m' \neq m \text{ et pour toute position } i
  $$

  

Idée pour la suite : introduire une variable secondaire qui compte le nombre de balles dans une main (pas possible ! parce que dans le cas d'un lancer multiplex on ne pourrait pas deviner qu'il faut la diminuer de plus de 1).

### Quatrième version

- Variables primaires :

  - $B_{b, t} \in \{1\}$ : la balle $b$ est quelque part au temps $t$.
  - $N_{t, m, i} \in \{1\}$ : la variable $S_{t, m, i}$ doit être initialisée.
  - $C_{t, m} \in \{1\}$ : configuration de la main $m$ obligatoire au temps $t$.

- Variables secondaires :

  - $P_{t, m, i}$ : on lui affecte une couleur $b$ (pour toute balle $b$).
  - $F_{t, b}$ : on lui affecte une couleur $0$ ou $1$ : la balle $b$ est en vol au temps $t$.
  - $S_{t, m, i}$ : on lui affecte une couleur $0$ ou $1$ : l'emplacement $(m, i)$ est utilisé ou non au temps $t$.
  - $E$ : on lui affecte une couleur $0$ ou $1$ : schéma interdit activé si $F : 1$.

- Couleurs :

  - $0$ et $1$ : Faux ou Vrai.
  - $b$ pour toute balle $b$.

- Règles :
  $$
  x_{T(t, b, \hmax)}^{m, h} \Rightarrow 
  \left\{\begin{array}{l}
  	P_{t + \hmax - h, m, i} : b\\
  	S_{t, m, i} : 1\\
  	N_{t, m, i}\\
  	B_{b, t}\\
  	E : 0
  \end{array}\right.
  $$

  $$
  P_{t, m, i} : b \Rightarrow
  \left\{\begin{array}{l}
  (P_{t + 1, m', i'} : b \text{ et } F_{t + 1, b} : 0) \text{ ou (pas sur la même ligne) } F_{t + 1, b} : 1\\
  S_{t, m, i} : 1\\
  N_{t, m, i}\\
  \end{array}\right.
  $$

- Schémas autorisés (pour chaque temps $t$ et chaque main $m$, l'un de ces schémas doit être choisi) :
  $$
  \begin{array}{c}
  C_{t, m} \;\wedge\; S_{t, m, 0} : 1 \;\wedge\; S_{t, m, 1} : 1 \;\wedge\; S_{t, m, 2} : 1 \;\wedge\; E : 1\\
  C_{t, m} \;\wedge\; S_{t, m, 0} : 1 \;\wedge\; S_{t, m, 1} : 1 \;\wedge\; S_{t, m, 2} : 0 \;\wedge\; E : 1\\
  C_{t, m} \;\wedge\; S_{t, m, 0} : 1 \;\wedge\; S_{t, m, 1} : 0 \;\wedge\; S_{t, m, 2} : 0 \;\wedge\; E : 1\\
  C_{t, m} \;\wedge\; S_{t, m, 0} : 0 \;\wedge\; S_{t, m, 1} : 0 \;\wedge\; S_{t, m, 2} : 0 \;\wedge\; E : 1\\
  \end{array}
  $$








$$
C_{t, m} \wedge S_{t, m, 0} : 0 \wedge S_{t, m, 1} : 0 \wedge S_{t, m, 2} : 0\\
C_{t, m} \wedge S_{t, m, 0} : 1 \wedge S_{t, m, 1} : 0 \wedge S_{t, m, 2} : 0 \wedge P_{t, m, 0} : b \wedge P_{t + 1, m, 0} : b\\
C_{t, m} \wedge S_{t, m, 0} : 1 \wedge S_{t, m, 1} : 0 \wedge S_{t, m, 2} : 0 \wedge P_{t, m, 0} : b \wedge P_{t + 1, m', 0} : b \wedge \\

C_{t, m} \wedge 

C_{t, m} \wedge S_{t, m, 0} : 1 \wedge S_{t, m, 1} : 1 \wedge S_{t, m, 2} : 0 \wedge P_{t, m, 0} : b_1 \wedge P_{t, m, 1} : b_2 \wedge P_{t + 1, m, 0} : b_2 \wedge P_{t + 1, m, 1} : b_1 \wedge S_{t + 1, m, 0} : 1 \wedge S_{t + 1, m, 1} : 1\\

C_{t, m} \wedge S_{t, m, 0} : 1 \wedge S_{t, m, 1} : 1 \wedge S_{t, m, 2} : 0 \wedge P_{t, m, 0} : b_1 \wedge P_{t, m, 1} : b_2 \wedge P_{t + 1, m, 0} : b_2 \wedge P_{t + 1, m, 1} : b_1 \wedge S_{t + 1, m, 0} : 1 \wedge S_{t + 1, m, 1} : 1\\

C_{t, m} \wedge S_{t, m, 0} : 1 \wedge S_{t, m, 1} : 1 \wedge S_{t, m, 2} : 0 \wedge P_{t, m, 0} : b_1 \wedge P_{t, m, 1} : b_2 \wedge P_{t + 1, m, 0} : b_2 \wedge P_{t + 1, m, 1} : b_1 \wedge S_{t + 1, m, 0} : 1 \wedge S_{t + 1, m, 1} : 1\\
$$






## Modifications sur l'algorithme M

Supposons $f$ une fonction de score d'une solution partielle. $f$ est telle que si $x'$ est la solution $x$ avec un choix supplémentaire à la fin, $0 \leq f(x') - f(x) \leq \frac{1}{n}$. On veut modifier l'algorithme M afin qu'il corresponde au schéma suivant :

1. $n \leftarrow $ majorant de la hauteur de l'arbre de recherche.

   $r \leftarrow n$.

2. Tant que ...

   1. $s$ est le score actuel de $x$.

   2. choisir la ligne $j$ pour la colonne $i$.

   3. $s \leftarrow f(x + i)$.
      $r \leftarrow r - 1$.

   4. Si $s + \frac{r}{n} < s_{\text{max}}$ : On annule le choix de la ligne $j$ et on choisira au prochain tour de boucle une autre ligne $j$ pour la colonne $i$.

      Sinon si on a une solution complète et $s > s_{\text{max}}$ alors $s_{\text{max}} \leftarrow s$.

      Sinon on continue la recherche de solution.

Ces modification semblent pouvoir être appliquées au début de l'étape M6, en première opération dans le If $x_l \neq i$. Ce que l'on appelle $j$ ci-dessus serait $x_l$.

