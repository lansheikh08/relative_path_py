"""Core implementation for relative_path_py.

Design decisions (read before extending):

1. We normalise paths to absolute form using os.path.abspath before splitting
   them. This means a trailing slash, redundant "." segments, or a ".." in the
   *input* are collapsed before we start reasoning about relatives. Without
   this, "/a/b/../c" and "/a/c" would be treated as different targets and
   produce a longer, more surprising result.

2. Cross-root situations (Windows drive letters, POSIX where one side is
   already absolute and the other is not after normalisation) cannot be
   expressed as a relative path made of ".." and named segments. We return
   the absolute target path in that case rather than raising. The caller can
   detect this by comparing the result's leading character (or os.path.isabs)
   if they need to branch on it. Raising would force every caller to wrap the
   call in a try/except for a situation that is perfectly well-defined — it
   just isn't *relative*.

3. We do not attempt to resolve symlinks. realpath would let us give a
   shorter answer in some cases, but it would also make the function depend
   on filesystem state at call time, which breaks reproducibility and makes
   testing a misery. If you need symlink-aware behaviour, call
   os.path.realpath yourself first.
"""

import os
import posixpath


def _split(path: str) -> list[str]:
    """Split a normalised absolute path into a clean list of components.

    We use posixpath semantics for the splitting logic even on Windows because
    os.path.split treats "C:\\" and "C:" inconsistently across versions, and
    ntpath.splitdrive leaves an empty string in the list that complicates the
    common-prefix comparison. By driving the path ourselves we get a single,
    predictable representation.
    """
    # os.path.abspath has already collapsed "." and ".." and made the path
    # absolute. We still strip any trailing separator so that "a/b" and
    # "a/b/" produce identical component lists.
    drive, rest = os.path.splitdrive(path)
    parts = [seg for seg in rest.split(os.sep) if seg]
    if drive:
        # Keep the drive as the first element so two paths on the same drive
        # share a common prefix of length >= 1, and two paths on *different*
        # drives share none.
        return [drive] + parts
    return parts


def relative_to(source: str, target: str) -> str:
    """Return the shortest relative path from *source* to *target*.

    Both *source* and *target* are interpreted as directories. If they live
    under different roots (different Windows drive letters, or one is absolute
    and the other cannot be made absolute in a compatible way) the absolute
    normalised *target* is returned, because no sequence of ".." can cross a
    root boundary.

    The result never contains a trailing separator and never contains "."
    segments. It may be empty, which means source and target refer to the same
    directory after normalisation.
    """
    src_abs = os.path.abspath(source)
    tgt_abs = os.path.abspath(target)

    src_parts = _split(src_abs)
    tgt_parts = _split(tgt_abs)

    # Different roots: we cannot walk from one to the other with ".." alone.
    # Fall back to the absolute target. This is the documented behaviour; it
    # is not an error.
    if src_parts and tgt_parts and src_parts[0] != tgt_parts[0]:
        return tgt_abs
    if bool(src_parts) != bool(tgt_parts):
        # One path reduced to an empty component list and the other did not.
        # On POSIX this does not happen for absolute inputs, but on Windows a
        # UNC root versus a drive root can produce it. Treat as cross-root.
        return tgt_abs

    # Find the length of the common prefix. We stop at the first differing
    # element; we do *not* use os.path.commonprefix because that operates on
    # strings and would think "/a/ab" and "/a/abc" share a longer prefix than
    # they really do at the path level.
    i = 0
    while i < len(src_parts) and i < len(tgt_parts) and src_parts[i] == tgt_parts[i]:
        i += 1

    # Climb out of the source directories that are below the common ancestor.
    up = [".."] * (len(src_parts) - i)
    # Descend into the target directories below the common ancestor.
    down = tgt_parts[i:]

    rel = os.sep.join(up + down)
    return rel


# Friendly alias. Some call sites read more naturally with a verb form.
resolve_relative = relative_to
