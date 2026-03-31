#!/bin/bash
cd /home/freemem/Projects/FreeMEMLang

echo "=== Compiling all examples ==="
echo ""

SUCCESS=0
FAILED=0
FAILED_LIST=""

for file in examples/*.dash; do
    name=$(basename "$file" .dash)
    printf "%-30s " "$name"

    if ./dash "$file" -o "bin/$name" > /tmp/compile_out.txt 2>&1; then
        if grep -q "Success" /tmp/compile_out.txt; then
            echo "[OK]"
            SUCCESS=$((SUCCESS + 1))
        else
            echo "[FAILED]"
            FAILED=$((FAILED + 1))
            FAILED_LIST="$FAILED_LIST $name"
        fi
    else
        echo "[FAILED]"
        FAILED=$((FAILED + 1))
        FAILED_LIST="$FAILED_LIST $name"
    fi
done

echo ""
echo "=== Results ==="
echo "Success: $SUCCESS"
echo "Failed:  $FAILED"
if [ -n "$FAILED_LIST" ]; then
    echo "Failed examples:$FAILED_LIST"
fi
