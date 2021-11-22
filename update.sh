echo "Downloading hashrate data"
curl -Lso "input/hashrate.csv" "https://etherscan.io/chart/hashrate?output=csv"

echo "Downloading block metadata from geth"
python block_updater.py

echo "Labeling block metadata"
python label_blocks.py

echo "Estimating emissions factors"
python estimate_emissions_factors.py

echo "Estimating daily power and daily emissions"
python estimate_power_emissions.py