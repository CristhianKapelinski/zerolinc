"""Device selection that survives a GPU this build of torch cannot drive.

``torch.cuda.is_available()`` answers whether a CUDA device was found, not whether
the installed torch carries kernels for it. A machine with an older card -- a Maxwell
Quadro (``sm_52``) against a torch built for Turing and newer -- passes that check and
then dies at the first kernel launch with ``no kernel image is available for execution
on the device``, a traceback the evaluator cannot act on and which stops the run
entirely. Compare the device's compute capability with the architectures this torch was
actually compiled for, and fall back to the CPU with a stated reason instead.

``ZEROLINC_DEVICE=cpu`` or ``=cuda`` overrides the decision, so the slow path can be
exercised deliberately on a machine that has a working GPU.
"""

from __future__ import annotations

import os
import sys

_ENV = "ZEROLINC_DEVICE"


def _note(message: str) -> None:
    print(f"NOTE: {message}", file=sys.stderr)


def _capability_covered(major: int, minor: int, archs: list[str]) -> bool:
    """Whether a torch compiled for ``archs`` can run on ``sm_{major}{minor}``.

    An exact ``sm_XY`` match is a compiled kernel. A ``compute_XY`` entry is PTX, which
    the driver JITs for any device at least that new -- forward compatible only, so it
    never rescues a device older than everything shipped.
    """
    if f"sm_{major}{minor}" in archs:
        return True
    for arch in archs:
        if not arch.startswith("compute_"):
            continue
        digits = arch[len("compute_"):].rstrip("af")
        if digits.isdigit() and (int(digits[:-1]), int(digits[-1])) <= (major, minor):
            return True
    return False


def cuda_usable() -> bool:
    """True when a CUDA device is present *and* this torch has kernels for it."""
    import torch

    forced = os.environ.get(_ENV, "").strip().lower()
    if forced == "cpu":
        _note(f"{_ENV}=cpu, so this runs on the CPU.")
        return False
    if forced == "cuda":
        _note(f"{_ENV}=cuda, so the GPU is used without checking its capability.")
        return True

    if not torch.cuda.is_available():
        return False
    try:
        major, minor = torch.cuda.get_device_capability(0)
        archs = list(torch.cuda.get_arch_list())
        name = torch.cuda.get_device_name(0)
    except Exception as exc:  # a present but unusable driver must not stop the run
        _note(f"the GPU could not be queried ({exc}); this runs on the CPU.")
        return False

    if _capability_covered(major, minor, archs):
        return True

    _note(
        f"{name} is sm_{major}{minor}, and this torch ({torch.__version__}) ships "
        f"kernels for {', '.join(archs) or 'no architecture'}. Running on the CPU "
        f"instead: slower, same numbers. Override with {_ENV}=cuda or {_ENV}=cpu."
    )
    return False
