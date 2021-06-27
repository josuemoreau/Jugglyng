---
jupytext:
  notebook_metadata_filter: rise
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
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

+++ {"nbgrader": {"grade": false, "grade_id": "cell-4911a792a82448d7", "locked": true, "schema_version": 3, "solution": false}, "slideshow": {"slide_type": "slide"}}

# Diaporamas interactifs avec Jupyter

+++ {"nbgrader": {"grade": false, "grade_id": "cell-8b77acf5d2044f9d", "locked": true, "schema_version": 3, "solution": false, "task": false}, "slideshow": {"slide_type": "fragment"}}

Dans cette feuille de travail, vous allez apprendre à utiliser Jupyter
et son extension [RISE](https://rise.readthedocs.io/) pour produire un
diaporama iteractif pour vos présentations orales.

+++ {"slideshow": {"slide_type": "subslide"}, "nbgrader": {"schema_version": 3, "solution": false, "grade": false, "locked": true, "task": false, "grade_id": "cell-e55a0f76366ee6ec"}}

## Utiliser un diaporama

Cette feuille de travail est en fait un diaporama!

- Lancez le diaporama, en cliquant sur l'icône <img src="rise-lancer.png" style='display:inline'>  de la barre d'outils.
- Parcourir l'ensemble du diaporama en explorant les fontionalités suivantes:
  - Naviguez avec les touches Page Haut et Page Bas
  - Consultez la documentation en cliquant sur l'icône `?`
  - Utilisez `Control +` et `Control -` pour adapter la taille des fontes
  - Cliquez sur l'icône <img src="rise-tableau-noir.png" style='display:inline'> pour lancer le tableau noir
  - Cliquez sur l'icône <img src="rise-tableau-noir.png" style='display:inline'> pour dessiner sur les diapos 
  - Cliquez sur l'icône <img src="rise-quitter.png" style='display:inline'> pour quitter le tableau noir ou les diapos

+++ {"slideshow": {"slide_type": "subslide"}, "nbgrader": {"schema_version": 3, "solution": false, "grade": false, "locked": true, "task": false, "grade_id": "cell-f3f6ad1e405c3005"}}

## Éditer un diaporama
- Quittez le diaporama
- Dans le menu «Affichage» (View), selectionnez «Barre d'outil de cellule» (Cell Toolbar) puis «Diaporama» (Diaporama).  
  Une barre de menu apparaît sur chaque cellule qui permet de définir son rôle:
  - Diapo: commence une nouvelle diapo
  - Sous-Diapo: commence une nouvelle sous-diapo (l'équivalent d'une sous-section)
  - Extrait: la cellule se rajoute à la diapo en cours
  - Sauter: la cellule n'apparaît pas dans les diapos
  - Note: idem, mais il est possible de faire afficher le contenu sur un deuxième écran
- Utilisez le bac à sable ci-dessous pour explorer les différents rôles et leur effet

+++ {"nbgrader": {"schema_version": 3, "solution": false, "grade": false, "locked": true, "task": false, "grade_id": "cell-cc4538c8e274a947"}, "slideshow": {"slide_type": "subslide"}}

## Pour aller plus loin
Consultez la documentation de [RISE](https://rise.readthedocs.io/)

+++

## Bac à sable
La suite de cette feuille contient une succession de cellules sans signification pour vous
servir de bac à sable. Vous pouvez en rajouter de nouvelles à votre convenance. 

Vous ne comprenez pas les textes? Pour savoir pourquoi, consultez
l'article [Lorem Ipsum](https://fr.wikipedia.org/wiki/Lorem_ipsum).

+++

## Bla bla bla
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

```{code-cell} ipython3
39 + 1
```

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.

```{code-cell} ipython3
40 + 1
```

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

+++

## The end of the universe

Vous êtes allé jusqu'ici? Bravo! Affectez 42 à la variable `ultime` pour marquer un point :-)

```{code-cell} ipython3
---
nbgrader:
  grade: false
  grade_id: cell-0fcaec8b81d7a78b
  locked: false
  schema_version: 3
  solution: true
  task: false
---
### BEGIN SOLUTION
ultime = 42
### END SOLUTION
```

```{code-cell} ipython3
---
nbgrader:
  grade: true
  grade_id: cell-963f3a9626ae1519
  locked: true
  points: 1
  schema_version: 3
  solution: false
  task: false
---
assert ultime == 42
```
