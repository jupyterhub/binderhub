export function NotFoundPage() {
  return (
    <>
      <div className="container text-center jumbotron">
        <h1>404: Not Found</h1>
      </div>
      <div className="container">
        <div className="row text-center">
          <h3>
            questions?
            <br />
            join the{" "}
            <a href="https://discourse.jupyter.org/c/binder">discussion</a>,
            read the{" "}
            <a href="https://mybinder.readthedocs.io/en/latest/">docs</a>, see
            the <a href="https://github.com/jupyterhub/binderhub">code</a>
          </h3>
        </div>
      </div>
    </>
  );
}
