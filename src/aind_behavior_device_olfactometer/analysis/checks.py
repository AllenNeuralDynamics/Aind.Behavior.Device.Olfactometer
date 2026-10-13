from .models import CheckResult, ProcessedSession

FLOW_TOLERANCE = 0.1


def check_end_session(processed: ProcessedSession) -> CheckResult:
    name = "end_session_exists"
    if processed.raw.has_end_session:
        return CheckResult(name, True, "EndSession event exists with data.")
    return CheckResult(name, False, "EndSession event does not exist. Session may be corrupted or not ended properly.")


def check_channels_configured(processed: ProcessedSession) -> CheckResult:
    name = "odor_channels_configured"
    if processed.calibrations:
        return CheckResult(name, True, f"Found {len(processed.calibrations)} (device, channel, mode) calibration(s).")
    return CheckResult(name, False, "No odor channel configurations found in the dataset.")


def check_repeat_counts(processed: ProcessedSession) -> CheckResult:
    name = "expected_repeats_found"
    expected = processed.raw.task_parameters.n_repeats_per_stimulus
    bad = [
        f"device {c.device_index} channel {c.channel_index} {c.mode}: {len(c.repeats)}"
        for c in processed.calibrations
        if len(c.repeats) != expected
    ]
    if bad:
        return CheckResult(name, False, f"Expected {expected} repeat(s), found " + "; ".join(bad))
    return CheckResult(name, True, f"All calibrations have the expected {expected} repeat(s).")


def check_flow_on_target(processed: ProcessedSession, tolerance: float = FLOW_TOLERANCE) -> CheckResult:
    name = "flow_within_tolerance"
    metrics = processed.metrics
    error = (metrics["flow_mean"] - metrics["flow_target"]).abs() > tolerance * metrics["flow_target"]
    bad = metrics[error | metrics["flow_mean"].isna()]
    if len(bad):
        details = "; ".join(_describe_flow(row) for row in bad.itertuples())
        return CheckResult(name, False, f"Flow outside {tolerance:.0%} of target: {details}")
    return CheckResult(name, True, f"Mean flow is within {tolerance:.0%} of target for all repeats.")


def run_checks(processed: ProcessedSession) -> list[CheckResult]:
    return [
        check_end_session(processed),
        check_channels_configured(processed),
        check_repeat_counts(processed),
        check_flow_on_target(processed),
    ]


def _describe_flow(row) -> str:
    return (
        f"device {row.device_index} channel {row.channel_index} {row.mode} repeat {row.repeat}: "
        f"{row.flow_mean:.1f} vs {row.flow_target:.1f}"
    )
