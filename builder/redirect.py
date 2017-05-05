from tornado import web, gen

class RedirectHandler(web.RequestHandler):
    def get(self):
        image = self.get_argument('image')
        url = self.settings['hub_redirect_url_template'].format(
            image=image
        )

        self.redirect(url)

