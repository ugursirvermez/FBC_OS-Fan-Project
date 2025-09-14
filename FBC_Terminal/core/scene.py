class Scene:
    def __init__(self, app): self.app = app
    def enter(self):  pass
    def exit(self):   pass
    def handle(self, e): pass
    def update(self, dt): pass
    def draw(self, s):    pass

class SceneManager:
    def __init__(self, app):
        self.app = app
        self.scene = None

    def switch(self, maker):
        """maker: class or lambda app: Scene"""
        if self.scene:
            self.scene.exit()
        self.scene = maker(self.app) if callable(maker) and not isinstance(maker, type) else maker(self.app)
        self.scene.enter()
