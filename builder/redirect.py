from tornado import web, gen

class RedirectHandler(web.RequestHandler):
    def get(self):
        image = self.get_argument('image')
        default_url = self.get_argument('default_url')
        url = self.settings['hub_redirect_url_template'].format(
            image=image,
            default_url=default_url
        )

        self.redirect(url)

