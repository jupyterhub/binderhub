import { useEffect, useState } from "react";
import { ImageBuilder } from "./components/builder.jsx";
import { useParams } from "react-router";
import { useSearchParams } from "react-router-dom";

export function LoadingPage({ baseUrl }) {
  const params = useParams();
  const spec = params["*"];

  const [searchParams, _] = useSearchParams();

  let urlPath = searchParams.get("urlpath");

  // Handle legacy parameters for opening URLs after launching
  // labpath and filepath
  if (searchParams.has("labpath")) {
    // Trim trailing / on file paths
    const filePath = searchParams.get("labpath").replace(/(\/$)/g, "");
    urlPath = `doc/tree/${encodeURI(filePath)}`;
  } else if (searchParams.has("filepath")) {
    // Trim trailing / on file paths
    const filePath = searchParams.get("filepath").replace(/(\/$)/g, "");
    urlPath = `tree/${encodeURI(filePath)}`;
  }

  const [isLaunching, setIsLaunching] = useState(false);

  useEffect(() => {
    // Start launching after the DOM has fully loaded
    setTimeout(() => setIsLaunching(true), 1);
  }, []);

  return (
    <>
      <ImageBuilder
        baseUrl={baseUrl}
        spec={spec}
        urlPath={urlPath}
        isLaunching={isLaunching}
        setIsLaunching={setIsLaunching}
      />
    </>
  );
}
