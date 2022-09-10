c.BinderHub.appendix = """
USER root
ENV BINDER_URL={binder_url}
ENV REPO_URL={repo_url}
RUN cd /tmp \
 && wget -q https://github.com/jupyterhub/binderhub/archive/main.tar.gz -O binderhub.tar.gz \
 && tar --wildcards -xzf binderhub.tar.gz --strip 2 */examples/appendix\
 && ./appendix/run-appendix \
 && rm -rf binderhub.tar.gz appendix
USER $NB_USER
"""
