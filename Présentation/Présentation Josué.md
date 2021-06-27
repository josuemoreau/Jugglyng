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

<!-- #region slideshow={"slide_type": "slide"} -->
# Combinatoire et jonglerie musicale
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "-"} -->
#### Josué Moreau et Léo Kulinski
<!-- #endregion -->

<!-- #region slideshow={"slide_type": "subslide"} -->
## Introduction
<!-- #endregion -->

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

```python
def hide_code_in_slideshow():   
    from IPython import display
    import binascii
    import os
    uid = binascii.hexlify(os.urandom(8)).decode()    
    html = """<div id="%s"></div>
    <script type="text/javascript">
        $(function(){
            var p = $("#%s");
            if (p.length==0) return;
            while (!p.hasClass("cell")) {
                p=p.parent();
                if (p.prop("tagName") =="body") return;
            }
            var cell = p;
            cell.find(".input").addClass("hide-in-slideshow")
        });
    </script>""" % (uid, uid)
    display.display_html(html, raw=True)
hide_code_in_slideshow()
```

```python
hide_code_in_slideshow()
print("hello")
```
