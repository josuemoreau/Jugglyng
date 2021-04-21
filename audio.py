from IPython.display import display, HTML, Javascript

class Audio():
    js_script_begin = """<script src="howler.js"></script>
		<script>
    		var sound = new Howl({
      			src: ['"""
    
    js_script_end = """']
			});
			
			sound.play()
		</script>"""
    
    def __init__(self, file):
        self.file = file
        self.js_script = self.js_script_begin + file + self.js_script_end
        self.html = HTML(self.js_script)
        self.disp = display("", display_id = True)
        
    def play(self):
        self.disp.update(self.html)