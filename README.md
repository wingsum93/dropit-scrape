# dropit website price scrapping
For user to fetch website product and price



## how to setup virtual environment

```sh
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
```


### Install Lib (win)
```sh
pip install -r requirements.txt
```


### Init postgresdb
```shell
python ./scraper/db.py
```







# Installation
Install python 3
Install ![Warp](https://www.warp.dev/)
Install postgres db (optional)
    Can be from container / install for machine





# Goal of the project
Fetch all items from the Devonshire Shop



## current issue
All product is around 13,628 items

But if we go to produc detail website, it take serval second to fetch data. So it take up to 5~6 second to fetch 1 product. The overall process take 68140 second (18.92 hours)