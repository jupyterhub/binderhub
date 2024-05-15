export function Header({ logoUrl, logoWidth }) {
  return (
    <>
      <div className="text-center">
        <img src={logoUrl} width={logoWidth} className="m-4" />
        <h5>Turn a Git repo into a collection of interactive notebooks</h5>
        <p>
          Have a repository full of Jupyter notebooks? With Binder, open those
          notebooks in an executable environment, making your code immediately
          reproducible by anyone, anywhere.
        </p>
        <p className="fw-lighter mt-8">
          New to Binder? Get started with a{" "}
          <a
            href="https://the-turing-way.netlify.app/communication/binder/zero-to-binder.html"
            target="_blank"
          >
            Zero-to-Binder tutorial
          </a>{" "}
          in Julia, Python, or R.
        </p>
      </div>
    </>
  );
}
