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
```

```python
from IPython.display import HTML
```

```python slideshow={"slide_type": "skip"}
from juggling_dlx_milp import *
```

```python slideshow={"slide_type": "skip"}
colors = ["blue", "red", "green", "yellow", "purple", "cyan", "magenta"]
sides = [-1, 1, 1]
```

<!-- #region slideshow={"slide_type": "slide"} -->
# Combinatoire et jonglerie musicale
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "-"} -->
#### Josué Moreau et Léo Kulinski
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "slide"} -->
## Introduction
<!-- #endregion -->

```python
HTML("""<video controls height="500" onloadstart="this.volume = 0.5">
  <source src="vincent_court.mp4">
</video>""")
```

<!-- #region slideshow={"slide_type": "slide"} -->
## Modèle de la jonglerie musicale
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
### Automate de jonglerie simple
<!-- #endregion -->

![Graphe de jonglerie musicale](slidefigs/figure-automate.png)


- Intro (1 min 30 - 2 min) Josué
- Modèle de la jonglerie musicale (aucune def, juste des figures) (
    - 1 slide : jonglerie simple (périodique)
    - 1 slide : multiplex
    - 1 slide : multihand
    - 1 slide : automate (jonglerie simple)
       ========================
    - 1 slide : jonglerie musicale
    - 1 slide : contraintes physiques
- Algo (6 min max) Josué
    - Automate (1 minute)
    - Exact Cover (1 minutes)
        - Exemple (avec ensemble)
            {a, b, c, d} { x_{... } l_{...} ... }
            
            {a, b}
            {c, d}
            {a, c}
            {c}
            {d}
        - Translation de l'exemple en forme matricielle
            1 1 0 0
            0 0 1 1 <- 
            1 0 1 0
            0 0 1 0 <- 
            0 0 0 1
            
            1 1 1 1
            
    - Codage des contraintes
    - Réduction vers MILP + Dancing Links
    - Mini démo
- OpenCV (6 min max) Léo
- Conclusion + Perspective communes + Qu'est-ce qu'on compte faire dans le mois à venir (2 min) Léo


### Démonstration


### Musique à jouer

```python
# Au clair de la lune
music = [( 1, "do"), ( 2, "do"), ( 3, "do"), 
         ( 4, "re"), ( 5, "mi"), ( 7, "re"), 
         ( 9, "do"), (10, "mi"), (11, "re"),
         (12, "re"), (13, "do")]
```

### Contraintes

```python
nb_hands = 2
max_height = 5
max_weight = 3
forbidden_multiplex = [(1, 2), (1, 3), (1, 4), (2, )]
```

```python
solve_and_simulate(music, nb_hands, max_height, max_weight, forbidden_multiplex, colors, sides, method="DLX")
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
