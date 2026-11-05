#!/bin/bash
# One file at a time, per the source-site rule in A5. URLs with tokens are never echoed.
cd "$1" || exit 1
UA="price-transparency-portfolio/0.1 (+https://github.com/LilCthulu/price-transparency-lakehouse)"
get() { # name url
  echo "START $1 $(date +%T)"
  curl -fsSL --retry 3 --retry-delay 30 --connect-timeout 30 -A "$UA" -o "$1" "$2"; echo "END $1 rc=$? $(date +%T)"
}
get vumc_main.csv "https://finance.vumc.org/assets/pub/pt/352528741_vanderbilt-university-medical-center_standardcharges.csv"
get vumc_clarksville.json "https://finance.vumc.org/assets/pub/pt/203500835_vanderbilt-clarksville-hospital_standardcharges.json"
get tristar_centennial.json "$(grep -o 'https://stctrprod[^"]*CENTENNIAL[^"]*' /c/Users/karat/Downloads/BUILD_CHECKLIST.md | head -1)"
get ascension_west.csv "https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620347580-1629025648_saint-thomas-west-hospital_standardcharges.csv"
get ascension_midtown.csv "https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620347580-1780778969_saint-thomas-west-hospital_standardcharges.csv"
ls -l
