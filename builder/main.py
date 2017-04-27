from tornado import web, gen


class MainHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")
