export function AboutPage({ aboutMessage, binderVersion }) {
  return (
    <div className="text-center">
      <h3>BinderHub</h3>
      <div>
        <p>
          This website is powered by{" "}
          <a href="https://github.com/jupyterhub/binderhub">BinderHub</a> v
          {binderVersion}
        </p>
        {aboutMessage && (
          <p dangerouslySetInnerHTML={{ __html: aboutMessage }}></p>
        )}
      </div>
    </div>
  );
}
