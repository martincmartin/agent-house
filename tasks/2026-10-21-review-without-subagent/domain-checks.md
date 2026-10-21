# Review checks for particular subjects

These review checks are true of particular projects, not of every review, so
they belong in each project's own `docs/`, with a line in its `AGENTS.md`
index: "before you review code, read …". The `review-general` skill tells a
reviewer to read the project's `AGENTS.md` and the docs it names.

Where each part could go:

- **Numerical optimization, integration, and control:** the project that uses
  kRPC and the trajectory code.
- **Slidev/Vue/TypeScript, SVG, and Flutter:** the Slidev parts are now in the
  `review-general` and `review-simplify` skills ("Slidev projects") and the `slidev-practices` skill. The
  Flutter part, and the investing illustrations, go to those projects.
- **Computer vision and watch analysis:** the watch-analysis project.

## The checks

**Numerical optimization, integration, and control (Python/NumPy/SciPy/kRPC)**

- Trace units, reference frames, vector orientation, state ordering, array shapes/dtypes, and scaling across interfaces. Check finite values and domain constraints where the program's contract requires them; account for legal sentinel infinities. An array annotation alone rarely proves its shape or physical meaning.
- Separate pure model/residual/control calculations from acquisition, clocks, RPC, and plotting when doing so enables replay or removes actual coupling. Preserve efficient local mutation and vectorization. Keep equations auditable against the stated model, with assumptions, sign conventions, and meaningful symbols.
- Check that solver status, feasibility, tolerances, integration error, and residuals are represented and interpreted before results drive downstream behavior. Distinguish convergence, feasibility, and optimality; a success flag or a necessary condition does not establish a global optimum. Do not invent Lawden/primer-vector conditions or certify the derivation without adequate evidence.
- For PID/control paths, inspect time units and clock choice, stale/out-of-order telemetry, saturation and integral handling, reset/mode transitions, and the deadline/failure response. State the concrete failure path; do not prescribe a control design or jitter policy without its model and timing constraints.
- Useful verification can include analytic limiting cases, independent residuals, conservation laws where applicable, tolerance refinement, deterministic replay, and dimensional checks. Recommend the smallest check that distinguishes the suspected error; self-consistency alone is not independent validation.

**Slidev/Vue/TypeScript, SVG, and Flutter**

- Preserve intentional visual detail and transitions. Keep semantic geometry, coordinate transforms, timing, and rendering understandable. Extract repeated mechanisms or shared mathematical rules when useful; do not force unrelated illustrations into a universal scene engine.
- Inspect component-instance SVG IDs and references, coordinate spaces, clipping, and transform ordering. Check re-entry, back navigation, cancellation, cleanup, and multiple instances for animations, listeners, timers, and subscriptions. Shared playback state needs an explicit owner.
- Use typed props/events and explicit state ownership. Avoid unnecessary watchers, mutable derived state, and parallel state-management mechanisms. Respect framework-required lifecycle and callback patterns; do not introduce an architecture solely because the app uses a framework.
- Builds and type checks do not prove appearance or timing. Where relevant, request targeted rendering at meaningful animation states or forward/back navigation checks. Keep authored SVG and numerical geometry editable; generated path volume alone does not justify modularization.
- For investing illustrations, make rate/percentage units, periods, nominal/real assumptions, and scenario inputs explicit. Review implementation and stated assumptions; do not claim financial-model validation from type checking.

**Computer vision and watch analysis**

- Trace pixel versus physical coordinates, color order, calibration, frame timestamps/rate, dropped frames, and angle conventions. Keep detection, association/tracking, and measurement distinctions explicit where their contracts differ.
- Represent missing detections and uncertainty without fabricated measurements or unexplained zeroes. Separate capture effects from replayable processing when useful. Do not claim physical accuracy from a successful OpenCV call; identify the calibration or reference measurement needed.
