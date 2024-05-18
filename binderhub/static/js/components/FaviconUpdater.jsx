import ProgressIcon from "../../images/favicon/progress.ico";
import FailIcon from "../../images/favicon/fail.ico";
import SuccessIcon from "../../images/favicon/success.ico";

import { PROGRESS_STATES } from "./Progress.jsx";
import { useEffect } from "react";
import { updateFavicon } from "../src/favicon";

export function FaviconUpdater({ progressState }) {
  useEffect(() => {
    switch (progressState) {
      case PROGRESS_STATES.FAILED: {
        updateFavicon(FailIcon);
        break;
      }
      case PROGRESS_STATES.SUCCESS: {
        updateFavicon(SuccessIcon);
        break;
      }
      case PROGRESS_STATES.BUILDING:
      case PROGRESS_STATES.PUSHING:
      case PROGRESS_STATES.LAUNCHING: {
        updateFavicon(ProgressIcon);
        break;
      }
    }
  }, [progressState]);
}
