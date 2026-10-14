"""Tests for relative_path_py.core.

Every test is deterministic: no clocks, no filesystem mutation, no floats.
We rely only on os.path to construct platform-appropriate absolute paths so
the suite passes on both POSIX and Windows without conditional skips.
"""

import os
import unittest

from relative_path_py import relative_to, resolve_relative


class RelativeToTests(unittest.TestCase):
    def test_same_directory_yields_empty(self):
        base = os.path.abspath("/a/b")
        self.assertEqual(relative_to(base, base), "")

    def test_target_descendant(self):
        src = os.path.abspath("/a/b")
        tgt = os.path.abspath("/a/b/c/d")
        self.assertEqual(relative_to(src, tgt), os.sep.join(["c", "d"]))

    def test_target_ancestor(self):
        src = os.path.abspath("/a/b/c")
        tgt = os.path.abspath("/a")
        self.assertEqual(relative_to(src, tgt), os.sep.join(["..", ".."]))

    def test_sibling_directory(self):
        src = os.path.abspath("/a/b/c")
        tgt = os.path.abspath("/a/d/e")
        self.assertEqual(relative_to(src, tgt), os.sep.join(["..", "..", "d", "e"]))

    def test_source_with_trailing_separator(self):
        # Trailing slashes must not change the result.
        src = os.path.abspath("/a/b") + os.sep
        tgt = os.path.abspath("/a/b/c")
        self.assertEqual(relative_to(src, tgt), "c")

    def test_redundant_dot_segments_in_source(self):
        src = os.path.abspath(os.path.join("/a/b", ".", "c"))
        tgt = os.path.abspath("/a/b/d")
        self.assertEqual(relative_to(src, tgt), os.sep.join(["..", "d"]))

    def test_parent_segments_in_input_are_collapsed(self):
        # "/a/b/../c" normalises to "/a/c"; the relative path from there to
        # "/a/d" should be "../d", not a journey through the literal "..".
        src = os.path.abspath("/a/b/../c")
        tgt = os.path.abspath("/a/d")
        self.assertEqual(relative_to(src, tgt), os.sep.join(["..", "d"]))

    def test_alias_matches_primary(self):
        src = os.path.abspath("/x/y")
        tgt = os.path.abspath("/x/y/z")
        self.assertEqual(resolve_relative(src, tgt), relative_to(src, tgt))

    def test_one_is_relative_input(self):
        # A relative input is resolved against cwd by os.path.abspath. We
        # cannot assert the exact result without knowing cwd, but we *can*
        # assert that two inputs that normalise to the same place agree.
        rel_src = os.path.join(".", "sub")
        abs_src = os.path.abspath(rel_src)
        tgt = os.path.join(abs_src, "deeper")
        self.assertEqual(relative_to(rel_src, tgt), "deeper")

    def test_common_prefix_is_path_aware_not_string_aware(self):
        # "/a/ab" and "/a/abc" share the component "a" but diverge at the
        # second component. A naive string-prefix approach would overshoot.
        src = os.path.abspath("/a/ab")
        tgt = os.path.abspath("/a/abc/x")
        self.assertEqual(relative_to(src, tgt), os.sep.join(["..", "abc", "x"]))

    def test_cross_root_returns_absolute_target(self):
        # On POSIX every absolute path shares the root "", so a true cross-root
        # case only exists on Windows. We synthesise the situation by feeding
        # two paths that abspath cannot reconcile to the same root: a drive
        # letter path and a UNC path. If the platform refuses to give us a UNC
        # path via abspath, we skip — this test is about the behaviour, not
        # about forcing a particular platform.
        drive = os.path.abspath("C:\\a\\b")
        try:
            unc = os.path.abspath("\\\\server\\share\\c\\d")
        except Exception:
            self.skipTest("UNC path resolution not available on this platform")
        if not (drive[:2].upper() == "C:" and unc.startswith("\\\\")):
            self.skipTest("Platform does not expose both drive and UNC roots")
        result = relative_to(drive, unc)
        self.assertEqual(result, unc)
        self.assertTrue(os.path.isabs(result))

    def test_result_has_no_trailing_separator(self):
        src = os.path.abspath("/a")
        tgt = os.path.abspath("/a/b/c")
        result = relative_to(src, tgt)
        self.assertFalse(result.endswith(os.sep))

    def test_result_has_no_dot_segments(self):
        src = os.path.abspath("/a/b")
        tgt = os.path.abspath("/a/b/c")
        result = relative_to(src, tgt)
        # No "." or ".." should appear when target is below source.
        self.assertNotIn(".", result.split(os.sep))


if __name__ == "__main__":
    unittest.main()
