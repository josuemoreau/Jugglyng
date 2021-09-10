---
jupyter:
  jupytext:
    notebook_metadata_filter: rise
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.11.3
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  rise:
    auto_select: first
    autolaunch: false
    centered: false
    controls: false
    enable_chalkboard: true
    height: 100%
    margin: 0
    maxScale: 1
    minScale: 1
    scroll: true
    slideNumber: true
    start_slideshow_at: selected
    transition: none
    width: 90%
---

```python slideshow={"slide_type": "skip"}
import sys
import os
import warnings

sys.path.insert(1, "Expérimentations/Juggling DLX")
os.chdir("../")
warnings.filterwarnings('ignore')

# zoom 125%
```

```python slideshow={"slide_type": "skip"}
from juggling_dlx_milp import *
```

```python slideshow={"slide_type": "slide"}
display_interface()
```

```python slideshow={"slide_type": "subslide"}

```

```python slideshow={"slide_type": "subslide"}

```

```python

```

<!-- #region slideshow={"slide_type": "skip"} -->
$$
\newcommand\ndo{\texttt{do}}
\newcommand\nre{\texttt{ré}}
\newcommand\nmi{\texttt{mi}}
\newcommand\hmax{h_{\text{max}}}
\newcommand\affect{\texttt{affect}}
\newcommand\oneaffect{\texttt{one-affect}}
\newcommand\weight{\texttt{weight}}
\newcommand\alt{\texttt{alt}}
\newcommand\catch{\texttt{catch}}
\newcommand\multiplex{\texttt{multiplex}}
\newcommand\double{\texttt{double}}
\newcommand\llbracket{[\![}
\newcommand\rrbracket{]\!]}
$$
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "slide"} -->
# Combinatoire et jonglerie musicale
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "-"} -->
#### Josué Moreau et Léo Kulinski
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "slide"} -->
## Introduction
<!-- #endregion -->

<center>
    <video id="intro_video" controls height="500" src="vincent_court.mp4" ></video>
</center>

<!-- #region slideshow={"slide_type": "slide"} -->
## Modèle de la jonglerie
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Jonglerie simple
- Une main.
- Lancers et rattrapages réguliers.
- Pas de balle en main.
- Jongle depuis / pour toujours.
- Balle rattrapée = Balle relancée.
- 0 ou 1 balle rattrapée à tout temps.

#### Exemple : Figure 312

<center>
    <img src="slidefigs/figure-3_1_2.png" width="1000"/>
</center>
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
#### Attention !
Périodicité pas toujours possible...

<center>
    <img src="slidefigs/figure-2_3_2.png" width="400"/>
</center>

<center>
    <img src="slidefigs/figure-3_0_3_0.png" width="350"/>
</center>
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Graphe de jonglerie simple

<center>
    <img src="slidefigs/figure-automate.png" width="700"/>
</center>
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Jonglerie multiplex
- Plusieurs balles rattrapables / lançables à tout temps.

#### Exemple : Figure [13]20

<center>
    <img src="slidefigs/figure-13_2_0.png" width="700"/>
</center>
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Jonglerie multimains
- Plusieurs mains.

#### Exemple : Figure $\Large\quad\begin{array}{lll}
        2_0 & 2_1 & 1_2 \\
        1_0 2_2 & 2_0 & 0 \\
        [1 3]_1 3_2 & 0 & 1_2
\end{array}
$

<center>
    <img src="slidefigs/figure-multihand.png" width="500"/>
</center>
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "slide"} -->
## Jonglerie musicale
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
- Plus de répétition des séquences.
- On ne jongle plus depuis / pour toujours.
- Distinction des balles dans la main.

$$\Large
\begin{pmatrix}
            1_{\ndo, 1} & 4_{\nmi, 1} & 1_{\ndo, 1} & 0 & 0           & 0 & 0           & 0           & 3_{\nre, 1} & 0 & 3_{\ndo, 1} & 0          \\
            4_{\nre, 1} & 1_{\ndo, 0} & 0           & 0 & 3_{\nre, 0} & 0 & 3_{\ndo, 0} & 3_{\nmi, 0} & 0           & 0 & 0           & 1_{\nre, 0} 
        \end{pmatrix}
$$
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Contraintes physiques de la jonglerie

- Hauteur maximale des lancers
- Lancers multiplex interdits (par exemple 1 et 3 en même temps)
- Position des balles dans les mains
    | 2 balles | 3 balles | 4 balles |
    |:--------:|:--------:|:--------:|
    | | | | 
    | <img width="94" src="slidefigs/figure-4.png" /> | <img width="200" src="slidefigs/figure-5.png" /> | <img width="200" src="slidefigs/figure-6.png" /> |

- On ne peut pas récupérer deux balles dans la même main au même instant.
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "slide"} -->
## Algorithme de composition
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
$$\normalsize
\{
            ( 0, \ndo), ( 1, \ndo), ( 2, \ndo), 
            ( 3, \nre), ( 4, \nmi), ( 6, \nre), 
            ( 8, \ndo), ( 9, \nmi), (10, \nre),
            (11, \nre), (12, \ndo)
        \}
$$
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "-"} -->
<center>
    <img width="1300" src="slidefigs/figure-automate_musical.png" />
</center>
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Exact Cover

$$\Large
\begin{array}{llc}
\begin{array}{ll}
    E & = \{a, b, c, d\}\\
    U_1 & = \{a, b\}\\
    U_2 & = \{b, c\}\\
    U_3 & = \{a, c, d\}\\
    U_4 & = \{a, d\}\\
    U_5 & = \{b\}\\
\end{array}
&
\hspace{1cm}
& 
M = 
\begin{pmatrix}
    1 & 1 & 0 & 0\\
    0 & 1 & 1 & 0\\
    1 & 0 & 1 & 1\\
    1 & 0 & 0 & 1\\
    0 & 1 & 0 & 0
\end{pmatrix}
\end{array}
$$

Existe-t-il un choix de lignes de $\Large M$ dont la somme est $\Large \begin{pmatrix} 1 & 1 & 1 & 1 \end{pmatrix}$ ?
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Exact Cover avec couleurs et multiplicités

- Éléments primaires : $\Large a, b$
- Bornes sur les éléments primaires : $\Large u_a = 0, v_a = 2 \qquad \Large u_b = 1, v_b = 1$
- Éléments secondaires : $\Large x, y$
- Couleurs : $\Large \{A, B\}$
- Lignes : $\Large\{a, (x, A)\} \qquad \{a, b, (x, A), (y, B)\} \qquad \{b, (x, B)\}$

Existe-t-il un choix de lignes tel que
- chaque élément primaire $\Large i$ est choisi entre $\Large u_i$ et $\Large v_i$ fois
- et au plus une couleur est affectée pour chaque élément secondaire ?
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Pré-traitement

$$\large
\{
            ( 1, \ndo), ( 2, \ndo), ( 3, \ndo), 
            ( 4, \nre), ( 5, \nmi), ( 7, \nre), 
            ( 9, \ndo), (10, \nmi), (11, \nre),
            (12, \nre), (13, \ndo)
        \}
$$

![Timeline](slidefigs/figure-pre_traitement.png)

$$\large
\begin{array}{llllll}
    T(0, \ndo, 1), & T(1, \ndo, 1), & T(2, \ndo, 1), &
    T(0, \nre, 4), & T(0, \nmi, 5), & T(4, \nre, 3),\\
    T(3, \ndo, 6), & T(5, \nmi, 5), & T(7, \nre, 4), &
    T(11, \nre, 1), & T(9, \ndo, 4)
\end{array}
$$
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Codage des contraintes

Colonnes d'affectation : $\Large\affect(T(t, b, \hmax), m, h) \in \llbracket 0, 1 \rrbracket$

Lignes : 1 ligne par colonne d'affectation

$\Large\oneaffect(T(t, b, \hmax)) \in \llbracket 1, 1 \rrbracket$

$$\Large
\affect(T(t, b, \hmax), m, h) \Rightarrow \oneaffect(T(t, b, \hmax))
$$

$\Large\weight(t, m) \in \llbracket 0, K \rrbracket$

$$\Large
\affect(T(t, b, \hmax), m, h) \Rightarrow \weight(t_1, m) \text{ pour tout } t_1 \in \llbracket t, t + \hmax - h \rrbracket
$$

$\Large\alt(t, b, m) \in \llbracket 0, 1 \rrbracket$

$$\Large
\affect(T(t, b, \hmax), m, h) \Rightarrow \alt(t, b, m)
$$
$$\Large
\affect(T(t, b, \hmax), m, 1) \Rightarrow \alt(t + \hmax, b, m)
$$
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Codage des contraintes

$\Large\double(t, m, h) \in \llbracket 0, 1 \rrbracket$

$$\Large
\affect(T(t, b, \hmax), m, h) \Rightarrow \double(t + \hmax - h, m, h)
$$

$\Large\multiplex(t, m, (h_1, h_2))$ et couleurs $\Large\llbracket 0, H \rrbracket$

$$\Large
\affect(T(t, b, \hmax), m, h_1) \Rightarrow \multiplex(t + \hmax - h, m, (h_1, h_2)) : h_1
$$

$$\Large
\affect(T(t, b, \hmax), m, h_2) \Rightarrow \multiplex(t + \hmax - h, m, (h_1, h_2)) : h_2
$$

$\Large\catch(t, m) \in \llbracket 0, 1 \rrbracket$

$$\Large
\affect(T(t, b, \hmax), m, h) \Rightarrow \catch(t + \hmax, m)
$$
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Résolution

#### Dancing Links
#### Programmation linéaire
$$\large
\begin{array}{lll}
    \textbf{Variables entières}: & \text{- $x_r$ pour toute ligne $r \in R$.}\\
    & \text{- $A_{i, c}$ pour tout $i \in S$ et pour tout $c$ tel qu'il existe une ligne}\\
    & \quad\text{$r' \in R$ qui affecte la couleur $c$ à la colonne secondaire $i$.}\\
    \textbf{Maximiser}: & \text{aucune fonction.}\\
    \textbf{Contraintes}: & \forall r \in R, \quad 0 \leq x_r \leq 1\\
    & \forall i \in S, c \in C,\quad 0 \leq A_{i, c} \leq 1\\
    & \forall i \in P, \quad \displaystyle u_i \leq \sum_{\begin{array}{cc} r \in R\\ \text{t.q. } i \text{ est affectée par }  r \end{array}} x_r \leq v_i\\
    & \text{$\forall i \in S, c \in C, r \in R \quad A_{i, c} \geq x_r$ si $i$ est affectée à la couleur $c$ dans $r$}\\
    & \text{$\forall i \in S, \quad \displaystyle\sum_{c \in C} A_{i, c} \leq 1$}
\end{array}
$$
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Démonstration
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "fragment"} -->
### Musique à jouer
<!-- #endregion -->

```python slideshow={"slide_type": "fragment"}
# Au clair de la lune
music = [( 1, "do"), ( 2, "do"), ( 3, "do"), 
         ( 4, "re"), ( 5, "mi"), ( 7, "re"), 
         ( 9, "do"), (10, "mi"), (11, "re"),
         (12, "re"), (13, "do")]
```

<!-- #region slideshow={"slide_type": "fragment"} -->
### Contraintes
<!-- #endregion -->

```python slideshow={"slide_type": "fragment"}
nb_hands = 2
max_height = 5
max_weight = 3
forbidden_multiplex = [(1, 2), (1, 3), (1, 4), (2, )]
```

```python slideshow={"slide_type": "fragment"}
solve_and_simulate(music, nb_hands, max_height, max_weight, forbidden_multiplex, colors, sides, method="MILP")
```

<!-- #region slideshow={"slide_type": "-"} -->
$$
\quad\\
\quad\\
\quad\\
\quad\\
\quad\\
\quad\\
\quad\\
\quad\\
\quad\\
\quad\\
\quad\\
$$
<!-- #endregion -->

```python slideshow={"slide_type": "slide"}

```

```python
solve_and_simulate(music, nb_hands, max_height, max_weight, forbidden_multiplex, colors, sides, method="MILP", optimize=True)
```

```python
solve_and_print(music, nb_hands, max_height, max_weight, forbidden_multiplex, method="DLX")
```

```python
solve_and_print(music, nb_hands, max_height, max_weight, forbidden_multiplex, method="MILP")
```
