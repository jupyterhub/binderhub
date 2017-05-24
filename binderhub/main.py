from tornado import web, gen


class MainHandler(web.RequestHandler):
    def get(self):
        self.render("index.html", url=None, ref='master', filepath=None, submit=False)


class ParameterizedMainHandler(web.RequestHandler):
    def get(self, provider_prefix, spec):
        providers = self.settings['repo_providers']
        if provider_prefix not in self.settings['repo_providers']:
            raise Exception('wat')
        provider = self.settings['repo_providers'][provider_prefix](config=self.settings['traitlets_config'], spec=spec)

        self.render(
            "index.html",
            url=provider.get_repo_url(),
            ref=provider.unresolved_ref,
            filepath=self.get_argument('filepath', None),
            submit=True
        )
