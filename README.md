# T2-Compiladores

## Executing With Makefile:
- Choose a example file from the `examples` folder and pass it as `FILE="example/file.ccc"`


```
make FILE="examples/ex1.ccc"
```

## With Python3:

```
pip3 install --user ply
pip3 install --user pprint

python3 semantic_syntatic_analyzer.py examples/ex1.ccc
```

## With Python < 3:

```
pip install --user ply
pip install --user pprint

python semantic_syntatic_analyzer.py examples/ex1.ccc
```
