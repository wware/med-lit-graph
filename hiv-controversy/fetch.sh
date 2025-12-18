#!/bin/bash

for pmcid in 2545367 269292 268988 322947 323687 238320 269383 329539 1307740; do
    curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=$pmcid&retmode=xml" \
         -o "PMC${pmcid}.xml"
    sleep 10
done
