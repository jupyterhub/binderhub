import ProgressIcon from "./img/favicon/progress.ico";
import FailIcon from "./img/favicon/fail.ico";
import SuccessIcon from "./img/favicon/success.ico";

import { PROGRESS_STATES } from "./Progress.jsx";

/**
 * @typedef {object} FaviconUpdaterProps
 * @prop {PROGRESS_STATES} progressState
 * @param {FaviconUpdaterProps} props
 */
export function FaviconUpdater({ progressState }) {
  let icon;
  switch (progressState) {
    case PROGRESS_STATES.FAILED: {
      icon = FailIcon;
      break;
    }
    case PROGRESS_STATES.SUCCESS: {
      icon = SuccessIcon;
      break;
    }
    case PROGRESS_STATES.BUILDING:
    case PROGRESS_STATES.PUSHING:
    case PROGRESS_STATES.LAUNCHING: {
      icon = ProgressIcon;
      break;
    }
  }

  return <link rel="icon" href={icon} type="image/x-icon"></link>;
}
