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
git pull origin
git branch -D flattened
git checkout --orphan flattened
cp backup/* output/
rm -rf backup
git add .
git commit -m "update"
git push origin +flattened:gh-pages
git checkout main
