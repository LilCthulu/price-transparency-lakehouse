import re, sys
t = open("PROJECT_CONTEXT.md", encoding="utf-8").read()
for head, dest in [("## A. `pipeline/stage.py`", "pipeline/stage.py"), ("## B. `pipeline/normalize.py`", "pipeline/normalize.py"), ("## C. `tests/test_normalize.py`", "tests/test_normalize.py")]:
    body = re.search(r"```python\n(.*?)\n```", t[t.index(head):], re.S).group(1)
    open(dest, "w", encoding="utf-8", newline="\n").write(body + "\n")
    print(dest, body.count("\n") + 1)
