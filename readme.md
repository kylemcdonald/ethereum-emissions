# Ethereum Emissions

Research into the daily energy consumption and emissions of the entire Ethereum network.

* [Ethereum Emissions Tracker](https://kylemcdonald.github.io/ethereum-emissions/)
* [Ethereum Emissions: A bottom-up estimate](https://github.com/kylemcdonald/ethereum-emissions/blob/main/McDonald-Ethereum-Emissions.pdf) (article)

## How to run

First, start downloading this [compressed snapshot of Ethereum blockchain metadata](https://storage.googleapis.com/ethereum-emissions/block_index-2022-09-15.zip) (158MB) and extract it inside the `cache/` folder.

Then, setup the Python environment. I used [Anaconda](https://www.anaconda.com/products/individual) to manage environments, and I created my environment like this:

```
conda create -n ethereum-emissions python=3.7
conda activate ethereum-emissions
pip install -r requirements.txt
```

You may also be able to use your system Python with pip, or this will probably work with other version management system as well.

Next, extract labels from the block metadata with `python label_blocks.py`. This step uses the `extraData` and the `miner` fields to make a guess about what region a block was mined in.

Then estimate emissions factors with `python estimate_emissions_factors.py`. This step maps each region to a distribution of electric grids, and takes a weighted average of the emissions factor for each grid.

Finally, estimate daily power and daily emissions with `python estimate_power_emissions.py`. This step uses the hashrate and hardware efficiency data to estimate the average daily power, and applies the emissions factors to estimate the daily emissions.

## Keeping up to date

If you want to run this code with the latest data, or you want to generate the block metadata index manually instead of starting from the snapshot, you will need direct access to an Ethereum node. As of 2021-11-20 running an Ethereum node requires 690GB of storage, and it can take 3-4 days to sync the entire chain even on a very fast network. This can be done by installing [geth](https://geth.ethereum.org/docs/install-and-build/installing-geth) and running it in the background. Then run `python block_updater.py` to extract the metadata from all blocks. This will take a few hours.

To run all these scripts in one go, starting with the `block_update.py`, run `bash update.sh`.

## Updating the article

To update the data and figures in the article, first run all the above scripts. Then run `bash update-article.sh`. This will run some scripts that save the updated figures in `article/images`, and it will save some numbers for the article in `output/results.txt`. Check the results in `output/results.txt` manually, then paste them into the appropriate section in `article/data.dat`.