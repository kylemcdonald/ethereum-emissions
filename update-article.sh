# download energy estimate data from digiconomist
curl -Lso "other-studies/digiconomist-energy.csv" "https://static.dwcdn.net/data/ocIBH.csv"

python package_emissions_factors.py
python package_power_emissions.py
python results.py > output/results.txt