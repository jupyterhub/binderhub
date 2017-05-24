from tornado import web, gen


class MainHandler(web.RequestHandler):
    def get(self):
        # Hacks!
        url = self.get_argument('url', '', True)
        ref = self.get_argument('ref', 'master', True)
        filepath = self.get_argument('filepath', '', True).replace('|', '#')
        submit = self.get_argument('submit', False, True)
        self.render(
            "index.html",
            url=url,
            ref=ref,
            filepath=filepath,
            submit=submit
        )
