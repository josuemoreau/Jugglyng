from IPython.display import display
import base64
import jp_proxy_widget


class Audio():
    def __init__(self, filename):
        self.widget = jp_proxy_widget.JSProxyWidget()
        self.js = "../../howler.js"

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

    def display(self):
        display(self.widget)

    def play(self):
        self.widget.element.sound.play()

    def pause(self):
        self.widget.element.sound.pause()
