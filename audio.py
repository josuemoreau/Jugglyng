from IPython.display import display, HTML, Javascript

# <script type="module">


# Init section
init_script = """<script type="module">
import * as THREE from 'https://unpkg.com/three@0.127.0/build/three.module.js';

const camera = new THREE.Camera();

const scene = new THREE.Scene();

const listener = new THREE.AudioListener();
camera.add(listener);

window.THREE = THREE;
window.listener = listener;
</script>"""
display(HTML(init_script))

js_script_model = """<script>
const sound{id} = new THREE.Audio(listener);
const audioLoader{id} = new THREE.AudioLoader();

audioLoader{id}.load('{file}', function(buffer) {{
    sound{id}.setBuffer(buffer);
    sound{id}.setLoop(false);
    sound{id}.setVolume(0.5);
}});

function play{id}() {{
    sound{id}.play();
}}

window.play{id} = play{id}
</script>"""


def new_id_fun():
    n = 0

    def f():
        nonlocal n
        n += 1
        return n
    return f


new_id = new_id_fun()


class Audio():
    def __init__(self, file):
        self.file = file
        self.id = new_id()

        self.js_script_init = js_script_model.format(id=self.id, file=file)
        display(HTML(self.js_script_init))

        self.html = HTML('<script>play%d();</script>' % self.id)
        self.disp = display("", display_id=True)

    def play(self):
        self.disp.update(Javascript("play{id}();".format(id=self.id)))
