wget --quiet -O gpu.json https://raw.githubusercontent.com/2miners/2cryptocalc-hashrates/master/gpu.json
echo "Name,Hashrate" > 2cryptocalc.csv
jq '.[] | .marketing_name + "," + (.algos.Ethash|tostring)' -r gpu.json >> 2cryptocalc.csv