grep Filename README.md | \
    sed -E 's|.*`(PMC[0-9]+)`.*$|curl -fL -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64)" -o \1.xml "https://pmc.ncbi.nlm.nih.gov/articles/\1/?report=xml\&format=text"|' | \
    bash
