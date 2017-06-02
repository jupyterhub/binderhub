from tornado import web, gen

class RedirectHandler(web.RequestHandler):
    def get(self):
        url = self.settings['hub_login_url'] + '?' + self.request.query

        self.redirect(url)

