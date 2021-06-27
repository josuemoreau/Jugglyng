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

```{code-cell} ipython3
---
slideshow:
  slide_type: skip
---
#Penser à régler taille chrome pour en un bouton afficher la vidéo à côté
```

+++ {"slideshow": {"slide_type": "slide"}}

# Analyse automatique de figures de jonglerie

```{code-cell} ipython3
---
slideshow:
  slide_type: fragment
---
import sys
sys.path.append('../Expérimentations/test_leo')
from balltracker_app import *
from post_detection import *
%config Completer.use_jedi = False
%load_ext autoreload
%autoreload 2
```

```{code-cell} ipython3
---
slideshow:
  slide_type: subslide
---
tracker = BallTracker(source='../../videos/vincent_court.mp4')
tracker.start()
```

```{code-cell} ipython3
tracker.load_config(path='vincent_court.json')
```

```{code-cell} ipython3
tracker.start_saving()
```

```{code-cell} ipython3
tracker.stop_saving()
tracker.save_config(path='presentation.json')
```

```{code-cell} ipython3
---
slideshow:
  slide_type: subslide
---
%matplotlib notebook
show_all_curves('presentation.json')
```

```{code-cell} ipython3
---
slideshow:
  slide_type: subslide
---
find_throws('presentation.json', ignore_nan=False)
```

```{code-cell} ipython3
from IPython.display import Video
Video("../../videos/vincent_court.mp4", height=500)
```

```{code-cell} ipython3
from IPython.display import HTML

a = HTML("""
<video alt="test" controls height="500" id="theVideo" muted>
  <source src="vincent_court.mp4">
</video>

<script>
video = document.getElementById("theVideo");
video.playbackRate = 0.5;
</script>
""")
```

```{code-cell} ipython3
%matplotlib inline
import matplotlib.pyplot as plt
import ipywidgets as widgets
import numpy as np

out1 = widgets.Output()
out2 = widgets.Output()
data1 = pd.DataFrame(np.random.normal(size = 50))
data2 = pd.DataFrame(np.random.normal(size = 100))

tab = widgets.Tab(children = [out1, out2])
tab.set_title(0, 'First')
tab.set_title(1, 'Second')
display(tab)

with out1:
    fig1, axes1 = plt.subplots()
    data1.hist(ax = axes1)
    plt.show(fig1)

with out2:
    fig2, axes2 = plt.subplots()
    data2.hist(ax = axes2)
    plt.show(fig2)
```

```{code-cell} ipython3
import ipywidgets as widgets
%matplotlib inline
out = widgets.Output()
with out:
    plt.plot([1, 2], [1, 2])
display(out)
```

```{code-cell} ipython3
display(out)
```

# Modélisation de la jonglerie

+++

## Jonglage simple
Hypothèse :
