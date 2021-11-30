#!/bin/bash

# start on main
git checkout main

# update all data and analysis
bash update.sh

# make copy of files
mkdir -p backup
mv output/daily-gw.csv output/daily-ktco2.csv backup
git reset --hard # need to do this otherwise we are asked to commit input/hashrate.csv
git checkout gh-pages
cp backup/* output/
git add -u output/
git commit -m "update"
git push origin gh-pages
git checkout main