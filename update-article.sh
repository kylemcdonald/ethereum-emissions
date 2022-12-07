# download energy estimate data from digiconomist
# latest version is available by clicking "download csv"
# at https://digiconomist.net/ethereum-energy-consumption
# most recently pulled on december 6, 2022

# this was the old way to grab the data
# curl -Lso "other-studies/digiconomist-energy.csv" "https://static.dwcdn.net/data/ocIBH.csv"

python package_emissions_factors.py
python package_power_emissions.py
python results.py > output/results.txt