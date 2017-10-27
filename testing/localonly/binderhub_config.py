from binderhub.repoproviders import FakeProvider

c.BinderHub.use_registry = False
c.BinderHub.builder_required = False
c.BinderHub.repo_providers = {'gh': FakeProvider}
c.BinderHub.tornado_settings.update({'fake_build':True})
