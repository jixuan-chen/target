import tqdm


def progress_iter(iterable, disable=False, feedback=None, total=None):
    """
    Iterate over `iterable`, reporting progress.

    If `feedback` is given, progress is reported through it instead of a
    console bar. `feedback` only needs a `setProgress(percent)` method
    (matching QGIS's QgsProcessingFeedback/QgsFeedback) and, optionally, an
    `isCanceled()` method to allow early termination - qgis itself is never
    imported here, so this works standalone too. Without `feedback`, falls
    back to a normal tqdm console progress bar. `disable=True` suppresses
    progress reporting entirely.
    """
    if disable:
        yield from iterable
        return

    if feedback is not None and hasattr(feedback, "setProgress"):
        if total is None:
            total = len(iterable) if hasattr(iterable, "__len__") else None
        for idx, item in enumerate(iterable):
            if hasattr(feedback, "isCanceled") and feedback.isCanceled():
                break
            yield item
            if total:
                feedback.setProgress(100 * (idx + 1) / total)
        return

    yield from tqdm.tqdm(iterable, total=total)
