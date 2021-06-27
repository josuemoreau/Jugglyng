---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.11.3
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

<!-- #region slideshow={"slide_type": "slide"} -->
# Analyse automatique de figures de jonglerie
<!-- #endregion -->

```python slideshow={"slide_type": "subslide"}
from IPython.display import Video
Video("../../videos/vincent_court.mp4", height=500)
```

<!-- #region slideshow={"slide_type": "subslide"} -->
# Modélisation de la jonglerie
<!-- #endregion -->

```python slideshow={"slide_type": "skip"}
import sys
sys.path.append('../Expérimentations/test_leo')
from balltracker_app import *
%config Completer.use_jedi = False
%load_ext autoreload
%autoreload 2
```

```python slideshow={"slide_type": "subslide"}
tracker = BallTracker(source='../../videos/vincent_court.mp4',
                   data_path='../Expérimentations/test_leo/vincent_court.json')
tracker.start()
```

```python
tracker.save_config(path='presentation.json')
```

```python
tracker.load_config(path='vincent_court.json')
```

```python
tracker.start_saving()
```

```python
tracker.stop_saving()
```

```python

```
