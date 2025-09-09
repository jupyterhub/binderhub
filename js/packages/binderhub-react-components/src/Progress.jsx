/**
 * @enum {string}
 */
export const PROGRESS_STATES = {
  WAITING: "Waiting",
  BUILDING: "Building",
  PUSHING: "Pushing",
  LAUNCHING: "Launching",
  SUCCESS: "Success",
  FAILED: "Failed",
};

const progressDisplay = {};
((progressDisplay[PROGRESS_STATES.WAITING] = {
  precursors: [],
  widthPercent: "10",
  label: "Waiting",
  className: "text-bg-danger",
}),
  (progressDisplay[PROGRESS_STATES.BUILDING] = {
    precursors: [PROGRESS_STATES.WAITING],
    widthPercent: "50",
    label: "Building",
    className: "text-bg-warning",
  }));

progressDisplay[PROGRESS_STATES.PUSHING] = {
  precursors: [PROGRESS_STATES.WAITING, PROGRESS_STATES.BUILDING],
  widthPercent: "30",
  label: "Pushing",
  className: "text-bg-info",
};

progressDisplay[PROGRESS_STATES.LAUNCHING] = {
  precursors: [
    PROGRESS_STATES.WAITING,
    PROGRESS_STATES.BUILDING,
    PROGRESS_STATES.PUSHING,
  ],
  widthPercent: "10",
  label: "Launching",
  className: "text-bg-success",
};

progressDisplay[PROGRESS_STATES.SUCCESS] =
  progressDisplay[PROGRESS_STATES.LAUNCHING];

progressDisplay[PROGRESS_STATES.FAILED] = {
  precursors: [],
  widthPercent: "100",
  label: "Failed",
  className: "text-bg-danger",
};

/**
 * @typedef {object} ProgressProps
 * @prop {PROGRESS_STATES} progressState
 * @param {ProgressProps} props
 */
export function Progress({ progressState }) {
  return (
    <div
      className="progress-stacked mb-2 border border-1"
      role="progressbar"
      style={{ height: "32px" }}
    >
      {progressState === null
        ? ""
        : progressDisplay[progressState].precursors
            .concat([progressState])
            .map((s) => (
              <div
                className={`progress-bar progress-bar-striped progress-bar-animated ${progressDisplay[s].className}`}
                style={{ width: `${progressDisplay[s].widthPercent}%` }}
                key={s}
              >
                <strong>{progressDisplay[s].label}</strong>
              </div>
            ))}
    </div>
  );
}
