export function HowItWorks() {
  return (
    <div>
      <h2 className="text-center mt-4">How it works</h2>

      <div className="row my-4">
        <div className="col-md-1 offset-md-2">
          <span
            className="circle-point"
            style={{
              color: "rgb(247, 144, 42)",
              borderColor: "rgb(247, 144, 42)",
            }}
          >
            1
          </span>
        </div>
        <div className="col-md-8">
          <h4>Enter your repository information</h4>
          Provide in the above form a URL or a GitHub repository that contains
          Jupyter notebooks, as well as a branch, tag, or commit hash. Launch
          will build your Binder repository. If you specify a path to a notebook
          file, the notebook will be opened in your browser after building.
        </div>
      </div>

      <div className="row my-4">
        <div className="col-md-1 offset-md-2">
          <span
            className="circle-point"
            style={{
              color: "rgb(204, 67, 101)",
              borderColor: "rgb(204, 67, 101)",
            }}
          >
            2
          </span>
        </div>
        <div className="col-md-8">
          <h4>We build a Docker image of your repository</h4>
          Binder will search for a dependency file, such as requirements.txt or
          environment.yml, in the repository's root directory (
          <a href="https://mybinder.readthedocs.io/en/latest/using.html#preparing-a-repository-for-binder">
            more details on more complex dependencies in documentation
          </a>
          ). The dependency files will be used to build a Docker image. If an
          image has already been built for the given repository, it will not be
          rebuilt. If a new commit has been made, the image will automatically
          be rebuilt.
        </div>
      </div>

      <div className="row my-4">
        <div className="col-md-1 offset-md-2">
          <span
            className="circle-point"
            style={{
              color: "rgb(41, 124, 184)",
              borderColor: "rgb(41, 124, 184)",
            }}
          >
            3
          </span>
        </div>
        <div className="col-md-8">
          <h4>Interact with your notebooks in a live environment!</h4> A{" "}
          <a href="https://jupyterhub.readthedocs.io/en/latest/">JupyterHub</a>{" "}
          server will host your repository's contents. We offer you a reusable
          link and badge to your live repository that you can easily share with
          others.
        </div>
      </div>
    </div>
  );
}
