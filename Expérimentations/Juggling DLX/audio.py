from IPython.display import display
import base64
import os
import jp_proxy_widget


_dirname = os.path.dirname(os.path.abspath(__file__))


class Audio():
    def __init__(self, filename, out=None):
        self.widget = jp_proxy_widget.JSProxyWidget()
        self.js = _dirname + "/howler.js"

        self.widget.load_js_files([self.js])

        f = open(filename, 'rb')
        data = f.read()
        encoded = base64.b64encode(data)

        self.url = 'data:audio/x-wav;base64,' + str(encoded)[2:-1]

        self.widget.js_init("""
            element.empty();

            element.sound = new Howl({
                src: [url]
            });
            """, url=self.url)

        if out is not None:
            with out:
                display(self.widget)
        else:
            display(self.widget)

    def play(self):
        self.widget.element.sound.play()

    def pause(self):
        self.widget.element.sound.pause()
