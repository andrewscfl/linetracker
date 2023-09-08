**LineTracker**

a small utility for counting lines of code in a codebase

**options**
```
-p: path to scan
-o: output file
-ie: ignore extension
-if: ignore folder
-iw: ignore whitespace
-q: quiet
-h: help           
```

**example**
```
python3 tracker.py -iw -if node_modules,.git,build,.next -p ../next-js-project
```