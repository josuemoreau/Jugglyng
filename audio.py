from IPython.display import display, HTML, Javascript

class Audio():
    js_script_begin = """<script type="module">
		import * as THREE from 'https://unpkg.com/three@0.127.0/build/three.module.js';
		
		const camera = new THREE.Camera();

		const scene = new THREE.Scene();

		// create an AudioListener and add it to the camera 
		const listener = new THREE.AudioListener();
		camera.add(listener); // create a global audio source

		const sound = new THREE.Audio(listener); // load a sound and set it as the Audio object's buffer 

		const audioLoader = new THREE.AudioLoader();
		audioLoader.load('"""
    
    js_script_end = """', function(buffer) {
			sound.setBuffer(buffer);
			sound.setLoop(false);
			sound.setVolume(0.5);
			sound.play();
		});
    </script>"""
    
    def __init__(self, file):
        self.file = file
        self.js_script = self.js_script_begin + file + self.js_script_end
        self.html = HTML(self.js_script)
        self.disp = display("", display_id = True)
        
    def play(self):
        self.disp.update(self.html)