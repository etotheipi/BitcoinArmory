rm -rf covhtml
mkdir covhtml
lcov --capture --directory . --output-file cov.info
genhtml cov.info --output-directory covhtml
rm cov.info
firefox covhtml/index.html
