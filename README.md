# relative_path_py

`relative_path_py` computes the shortest relative path from one directory to another, normalising redundant `.` and `..` segments in the inputs first and handling different roots (such as distinct Windows drive letters) by returning the absolute target instead of raising.

```python
from relative_path_py import relative_to, resolve_relative

# "/a/b/c" from "/a/b"
print(relative_to("/a/b", "/a/b/c"))          # -> "c"

# climb out of two directories and back down into a sibling
print(relative_to("/a/b/c", "/a/d/e"))         # -> "../../d/e"

# resolve_relative is an alias for readability at the call site
print(resolve_relative("/a/b", "/a/b/c"))     # -> "c"
```

## Why this exists

The standard library's `os.path.relpath` does most of this, but it raises `ValueError` when the two paths sit on different roots (for example `C:\` and `D:\` on Windows). In real code that deals with user-supplied paths, a cross-root situation is not exceptional — it is just a path you cannot reach by walking `..`. This library returns the absolute target in that case, so callers that are happy to fall back to an absolute path need no `try/except` wrapper, and callers that need to branch can check `os.path.isabs` on the result.

The trade-off: the result type is a string either way, so a cross-root result is indistinguishable in type from a relative one. If you need to know which happened, inspect the first character or call `os.path.isabs`.

## Edge you will hit

The function does not resolve symlinks. If `source` is a symlink to `target`'s parent, the result reflects the literal path you passed, not the filesystem truth. Call `os.path.realpath` on both arguments first if you need symlink-aware behaviour; doing it inside the library would make the result depend on filesystem state at call time and break reproducibility.

On Windows, a drive-letter path and a UNC path (`\\\server\share\...`) are treated as different roots; the absolute target is returned. Two paths on the same drive, even with different casing, share a root.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

