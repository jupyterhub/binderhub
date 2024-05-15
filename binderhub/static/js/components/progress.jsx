export const PROGRESS_STATES = {};
PROGRESS_STATES.WAITING = {
  precursors: [],
  widthPercent: "10",
  label: "Waiting",
  className: "text-bg-danger",
};
PROGRESS_STATES.BUILDING = {
  precursors: [PROGRESS_STATES.WAITING],
  widthPercent: "50",
  label: "Building",
  className: "text-bg-warning",
};
PROGRESS_STATES.PUSHING = {
  precursors: [PROGRESS_STATES.WAITING, PROGRESS_STATES.BUILDING],
  widthPercent: "30",
  label: "Pushing",
  className: "text-bg-info",
};
PROGRESS_STATES.LAUNCHING = {
  precursors: [
    PROGRESS_STATES.WAITING,
    PROGRESS_STATES.BUILDING,
    PROGRESS_STATES.PUSHING,
  ],
  widthPercent: "10",
  label: "Launching",
  className: "text-bg-success",
};
PROGRESS_STATES.FAILED = {
  precursors: [],
  widthPercent: "100",
  label: "Failed",
  className: "text-bg-danger",
};

export function Progress({ state }) {
  return (
    <div
      className="progress-stacked mb-2"
      role="progressbar"
      style={{ height: "24px" }}
    >
      {state === null
        ? ""
        : state.precursors.concat([state]).map((s) => (
            <div
              className={`progress-bar progress-bar-striped progress-bar-animated ${s.className}`}
              style={{ width: `${s.widthPercent}%` }}
            >
              <strong>{s.label}</strong>
            </div>
          ))}
    </div>
  );
}
