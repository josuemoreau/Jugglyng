# Résolution du problème avec Exact Cover

$$
\newcommand\hmax{h_{\text{max}}}
$$

## Le problème

Étant donné une musique, trouver toutes les séquences de jonglerie jouant cette musique avec $M$ main et respectant les contraintes suivantes :

1. les temps de vols sont d'au plus $H$
2. il y a au plus $K$ balles dans chaque main, à chaque instant
3. certains enchaînements de hauteurs de lancers sont interdits
4. certains lancers multiplex (sans compter les balles restant en main) sont interdits

## Représentation d'un lancer

Dans cette réduction, on considère qu'un lancer est un élément composé de deux parties : une partie où la balle est dans la main et une partie où la balle est en vol. Dans la suite, on notera un lancer de la manière suivante : $T(t, b, h_{\text{max}})$. Le temps $s$ pendant lequel la balle reste dans la main et la main dans laquelle se trouve la balle pendant ce temps sont les données que l'on souhaite faire varier pour essayer de respecter un ensemble de contraintes fixées par le jongleur.

![lancer](/home/josue/Documents/Scolaire/M1/Stage/Notes/lancer.svg)

## 1ère étape : Calculer les hauteurs maximales

La première étape est de calculer, pour chaque lancer, la hauteur maximale. Avant d'expliquer comment calculer ces nombres, on pose l'hypothèse : il y a au plus une balle pour chaque note. Cette hypothèse implique qu'on peut nommer les balles par la note qu'elles jouent. Elle permet aussi de simplifier l'algorithme.

L'algorithme est donc le suivant :

- placer les notes sur un diagramme de jonglerie aux instants où elles doivent être jouées
- relier tout couple d'instant où la même balle doit être jouée par un lancer
- les hauteurs maximales pour chacun de ces lancers sont donc leur durées sur le diagramme de jonglerie
- cet algorithme renvoie une liste de lancers de la forme $T(t, b, h_{\text{max}})$

![hauteurs max](/home/josue/Documents/Scolaire/M1/Stage/Notes/hauteurs max.svg)

## 2ème étape : Énumérer toutes les configurations de mains respectant les contraintes

Pour énumérer toutes ces configurations, on présente une réduction du problème vers Exact Cover généralisé, c'est-à-dire que le nombre d'éléments choisis dans la colonne $i$ doit être dans un intervalle $[a_i, b_i]$ (contrairement à Exact Cover classique où cette somme doit être égale à 1).

### Représentation initiale des lancers

Afin de représenter les lancers et les possibilités sans contraintes dans Exact Cover généralisé on introduit les colonnes suivantes pour tout lancer $T(t, b, \hmax)$ :

$x_{T(t, b, \hmax)}^{m, h} \in [0, 1] \;\forall m \in [1, M], \;\forall h \in [1, \hmax]$: le lancer $T(t, b, \hmax)$ est affecté à la main $m$ qui garde la balle $b$ pendant $\hmax - h$ temps avant de la lancer pour une hauteur $h$.

Par la suite, lorsqu'on introduit des variables, on va introduire des règles d'affectations de la forme $a \Rightarrow b$, celle-ci signifie que si la colonne $a$ est affectée dans une certaine ligne, alors la colonne $b$ doit aussi l'être dans cette ligne. Concernant ces lignes, il y en a une pour chaque colonne $x_{T(t, b, \hmax)}^{m, h}$ qui affecte uniquement cette colonne. On introduit maintenant avec cette notation l'ensemble de colonnes suivant:

$l_{T(t, b, \hmax)} \in [1, 1]$: le lancer $T(t, b, \hmax)$ est affecté à exactement une main et une durée de main.
$$
x_{T(t, b, \hmax)}^{m, h} \Rightarrow l_{T(t, b, \hmax)}
$$

### Contrainte 1

On génère uniquement les colonnes $x_{T(t, b, \hmax)}^{m, h}$ telles que $h \leq \min(\hmax, H)$.

### Contrainte 2

$w_t^m \in [0, K] \;\forall t, \;\forall m \in [1, M]$: la main $m$ contient, à l'instant $t$, la balle choisie dans la ligne où cette variable est affectée.
$$
x_{T(t, b, \hmax)}^{m, h} \Rightarrow w_{t'}^m \;\forall t' \in [t, t+\hmax-h]
$$

### Contrainte 3

$I_{t, h}^{m} \in [0, 1] \;\forall t, \;\forall m \in [1, M], \;\forall h \in [1, H]$: il est interdit pour la main $m$ de faire un lancer de hauteur $h$ à l'instant $t$.

Supposons $h_1 \rightarrow h_2$ interdit.
$$
x_{T(t, b, \hmax)}^{m, h_1} \Rightarrow I_{t + 1, h_2}^{m} 
\hspace{1cm}\text{et}\hspace{1cm} 
x_{T(t', b', \hmax')}^{m', h_2} \Rightarrow I_{t' + \hmax' - h_2, h_2}^{m'}
$$

### Contrainte 4

$M_{t, c}^m \in [0, |c| - 1] \;\forall t, \;\forall m \in [1, M], \;\forall c \text{ un lancer multiplex interdit}$: il est interdit d'effectuer tous les lancers de hauteur $h \in c$ au même instant $t$.
$$
x_{T(t, b, \hmax)}^{m, h} \wedge h \in c \Rightarrow M_{t+\hmax-h, c}^m
$$

## Réduction de Exact Cover généralisé vers Integer Linear Programming

Dans un premier temps, on souhaite trouver rapidement une solution à l'instance Exact Cover généralisée énoncée précédemment.

### Instance de Exact Cover généralisé

- Un ensemble de colonnes ($x_{T(t, b, \hmax)}^{m, h}$, $l_{T(t, b, \hmax)}$, ...) avec, pour chaque colonne, les bornes minimum et maximum sur le nombre d'éléments choisis dans cette colonne.
- Un ensemble $R$ de lignes qui affectent chacune certaines colonnes.

### Instance de ILP correspondante

- variables : $v_r$ pour chaque ligne $r \in R$

- fonction objectif : aucune !

- contraintes :

  Pour toute colonne $C$:
  $$
  \min(C) \leq \sum_{\begin{array}{cc}r \in R\\C \text{ est affectee par }r\end{array}} v_r \leq \max(C)
  $$
  

